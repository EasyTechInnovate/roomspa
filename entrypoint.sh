#!/bin/bash

# Exit on any error
set -e

echo "===== STARTING ENTRYPOINT SCRIPT $(date) ====="

# Wait for database to be ready
echo "🔄 Waiting for database..."
max_retries=30
counter=0
while ! pg_isready -h db -U postgres 2>/dev/null; do
    counter=$((counter+1))
    if [ $counter -eq $max_retries ]; then
        echo "❌ Failed to connect to database after $max_retries attempts"
        exit 1
    fi
    echo "⏳ Database not ready, waiting... ($counter/$max_retries)"
    sleep 1
done
echo "✅ Database is ready!"

# Collect static files
echo "🔄 Collecting static files..."
python manage.py collectstatic --noinput
echo "✅ Static files collected"

# Auto-detect installed apps and create universal schema fix script
echo "🔧 Generating schema inspection script..."

cat > schema_fix.py << 'EOF'
import os
import sys
import django
from django.conf import settings
from django.db import connection, models
from django.apps import apps

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Spa.settings')
django.setup()

# Function to execute SQL safely
def execute_sql(cursor, sql, params=None):
    try:
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        return True
    except Exception as e:
        print(f"❌ SQL Error: {e}")
        return False

def get_db_tables():
    """Get all tables in the database"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT tablename FROM pg_catalog.pg_tables
            WHERE schemaname != 'pg_catalog' AND schemaname != 'information_schema'
        """)
        return [row[0] for row in cursor.fetchall()]

def get_model_fields(model):
    """Get field information for a model"""
    fields = []
    for field in model._meta.fields:
        field_type = None
        
        # Map Django field types to PostgreSQL types
        if isinstance(field, models.CharField) or isinstance(field, models.TextField):
            max_length = getattr(field, 'max_length', None)
            if max_length:
                field_type = f"VARCHAR({max_length})"
            else:
                field_type = "TEXT"
        elif isinstance(field, models.IntegerField) or isinstance(field, models.AutoField):
            field_type = "INTEGER"
        elif isinstance(field, models.BooleanField):
            field_type = "BOOLEAN"
        elif isinstance(field, models.DateField):
            field_type = "DATE"
        elif isinstance(field, models.DateTimeField):
            field_type = "TIMESTAMP WITH TIME ZONE"
        elif isinstance(field, models.DecimalField):
            max_digits = getattr(field, 'max_digits', 10)
            decimal_places = getattr(field, 'decimal_places', 2)
            field_type = f"NUMERIC({max_digits},{decimal_places})"
        elif isinstance(field, models.FloatField):
            field_type = "DOUBLE PRECISION"
        elif isinstance(field, models.EmailField):
            field_type = "VARCHAR(254)"
        elif isinstance(field, models.ForeignKey) or isinstance(field, models.OneToOneField):
            # For ForeignKey, usually an integer (might be UUID or other in some cases)
            field_type = "INTEGER"
        elif isinstance(field, models.ManyToManyField):
            # M2M fields typically use separate tables, skip for direct column creation
            continue
        else:
            # Default to TEXT for unknown types
            field_type = "TEXT"
            
        fields.append({
            'name': field.column,
            'type': field_type,
            'null': field.null,
            'related_model': field.related_model.__name__ if hasattr(field, 'related_model') and field.related_model else None
        })
    
    return fields

def check_and_fix_schema():
    """Check all models and fix schema issues"""
    print("🔍 Inspecting models and database schema...")
    
    db_tables = get_db_tables()
    print(f"Found {len(db_tables)} tables in database")
    
    with connection.cursor() as cursor:
        # Process each installed app and its models
        fixed_issues = 0
        for app_config in apps.get_app_configs():
            print(f"\n📦 Checking app: {app_config.label}")
            
            for model in app_config.get_models():
                table_name = model._meta.db_table
                print(f"  📋 Model: {model.__name__} (Table: {table_name})")
                
                # Check if table exists
                if table_name.lower() not in [t.lower() for t in db_tables]:
                    print(f"  ⚠️ Table {table_name} does not exist in database!")
                    continue
                
                # Get columns that should be in the model
                model_fields = get_model_fields(model)
                
                # Get existing columns in the database table
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = %s
                """, [table_name.lower()])
                
                db_columns = {row[0]: {'type': row[1], 'nullable': row[2]} for row in cursor.fetchall()}
                
                # Check each field in the model
                for field in model_fields:
                    column_name = field['name']
                    
                    if column_name.lower() not in [c.lower() for c in db_columns.keys()]:
                        print(f"  ⚠️ Missing column: {column_name} in table {table_name}")
                        
                        # Generate SQL for adding the column
                        null_clause = "" if field['null'] else "NOT NULL DEFAULT ''"
                        sql = f"ALTER TABLE \"{table_name}\" ADD COLUMN \"{column_name}\" {field['type']} {null_clause}"
                        
                        print(f"  🔧 Adding column with: {sql}")
                        
                        if execute_sql(cursor, sql):
                            print(f"  ✅ Added column {column_name} to {table_name}")
                            fixed_issues += 1
                        else:
                            print(f"  ❌ Failed to add column {column_name}")
    
    if fixed_issues > 0:
        print(f"\n🔧 Fixed {fixed_issues} schema issues")
    else:
        print("\n✅ No schema issues detected")

# Run the schema check and fix
check_and_fix_schema()
EOF

# Run the schema inspection and fixing script
echo "🔄 Detecting and fixing schema issues..."
python schema_fix.py

# Generate migrations for all apps
echo "🔄 Creating migrations for all apps..."
django_apps=$(python -c "
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Spa.settings')
django.setup()
from django.apps import apps
print(' '.join(app.label for app in apps.get_app_configs() if not app.name.startswith('django')))
")

for app in $django_apps; do
    echo "📦 Creating migrations for $app..."
    python manage.py makemigrations $app || echo "⚠️ Could not create migrations for $app"
done

# Show migration status before applying
echo "📋 Current migration status:"
python manage.py showmigrations

# Apply migrations with detailed output
echo "🔄 Applying migrations..."
python manage.py migrate --verbosity 2
echo "✅ Migrations applied"

# Show migration status after applying
echo "📋 Updated migration status:"
python manage.py showmigrations

# Start server
echo "🚀 Starting server..."
echo "===== ENTRYPOINT SCRIPT COMPLETED $(date) ====="
exec daphne -b 0.0.0.0 -p 8000 Spa.asgi:application