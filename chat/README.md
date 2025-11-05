# WebSocket API Documentation

This documentation covers the usage of two WebSocket endpoints for real-time chat and location sharing between customers and therapists.

## Overview

The application provides two main WebSocket consumers:
- **ChatConsumer**: Handles real-time messaging between customers and therapists
- **LocationConsumer**: Handles real-time location sharing from therapists to customers

## Authentication

Both WebSocket endpoints require JWT authentication. The token can be provided in two ways:

### Query Parameter
```
ws://your-domain/ws/chat/123/456/?token=your_jwt_token
```

### Authorization Header
```
Authorization: Bearer your_jwt_token
```

## WebSocket Endpoints

### 1. Chat WebSocket

**Endpoint:** `ws://your-domain/ws/chat/{customer_id}/{therapist_id}/`

#### Connection Requirements
- User must be authenticated
- Customer users can only connect to their own customer_id
- Therapist users can only connect to their own therapist_id
- Both customer_id and therapist_id must be valid

#### Sending Messages

**Client → Server**
```json
{
  "message": "Hello, how are you today?"
}
```

**Fields:**
- `message` (string, required): The message content. Empty messages are ignored.

#### Receiving Messages

**Server → Client**
```json
{
  "type": "message",
  "message": "Hello, how are you today?",
  "sender_id": "123",
  "message_id": "789",
  "timestamp": "2024-01-15T10:30:00.123456Z"
}
```

**Fields:**
- `type`: Always "message"
- `message`: The message content
- `sender_id`: ID of the user who sent the message
- `message_id`: Unique identifier for the message
- `timestamp`: ISO format timestamp when the message was created

#### Usage Example

```javascript
// Connect to chat WebSocket
const chatSocket = new WebSocket(
    'ws://localhost:8000/ws/chat/123/456/?token=' + jwtToken
);

// Handle incoming messages
chatSocket.onmessage = function(event) {
    const data = JSON.parse(event.data);
    if (data.type === 'message') {
        console.log(`Message from ${data.sender_id}: ${data.message}`);
        // Display message in chat UI
        displayMessage(data.message, data.sender_id, data.timestamp);
    }
};

// Send a message
function sendMessage(messageText) {
    if (chatSocket.readyState === WebSocket.OPEN) {
        chatSocket.send(JSON.stringify({
            'message': messageText
        }));
    }
}

// Handle connection events
chatSocket.onopen = function(event) {
    console.log('Chat WebSocket connected');
};

chatSocket.onclose = function(event) {
    console.log('Chat WebSocket disconnected:', event.code);
};

chatSocket.onerror = function(error) {
    console.error('Chat WebSocket error:', error);
};
```

### 2. Location WebSocket

**Endpoint:** `ws://your-domain/ws/location/{customer_id}/{therapist_id}/`

#### Connection Requirements
- User must be authenticated
- Customer users can only connect to their own customer_id
- Therapist users can only connect to their own therapist_id
- Both customer_id and therapist_id must be valid

#### Sending Location (Therapists Only)

**Client → Server**
```json
{
  "latitude": 40.7128,
  "longitude": -74.0060
}
```

**Fields:**
- `latitude` (number, required): Latitude coordinate
- `longitude` (number, required): Longitude coordinate

**Note:** Only therapists can send location updates. Customer location updates are ignored.

#### Receiving Location Updates

**Server → Client**
```json
{
  "type": "location",
  "latitude": 40.7128,
  "longitude": -74.0060,
  "therapist_id": "456"
}
```

**Fields:**
- `type`: Always "location"
- `latitude`: Latitude coordinate
- `longitude`: Longitude coordinate
- `therapist_id`: ID of the therapist sharing the location

#### Usage Example

```javascript
// Connect to location WebSocket
const locationSocket = new WebSocket(
    'ws://localhost:8000/ws/location/123/456/?token=' + jwtToken
);

// Handle incoming location updates (for customers)
locationSocket.onmessage = function(event) {
    const data = JSON.parse(event.data);
    if (data.type === 'location') {
        console.log(`Therapist ${data.therapist_id} location: ${data.latitude}, ${data.longitude}`);
        // Update map with therapist location
        updateMapLocation(data.latitude, data.longitude);
    }
};

// Send location update (for therapists only)
function sendLocation(lat, lng) {
    if (locationSocket.readyState === WebSocket.OPEN && userRole === 'therapist') {
        locationSocket.send(JSON.stringify({
            'latitude': lat,
            'longitude': lng
        }));
    }
}

// Get and send current location (therapists)
function shareCurrentLocation() {
    if (navigator.geolocation && userRole === 'therapist') {
        navigator.geolocation.getCurrentPosition(
            function(position) {
                sendLocation(
                    position.coords.latitude,
                    position.coords.longitude
                );
            },
            function(error) {
                console.error('Error getting location:', error);
            }
        );
    }
}

// Handle connection events
locationSocket.onopen = function(event) {
    console.log('Location WebSocket connected');
};

locationSocket.onclose = function(event) {
    console.log('Location WebSocket disconnected:', event.code);
};
```

## Error Codes

WebSocket connections may be closed with the following error codes:

- **4000**: Missing required parameters (customer_id or therapist_id)
- **4001**: User not authenticated
- **4003**: Authorization error (user trying to access unauthorized conversation)

## Complete Integration Example

```javascript
class TherapyWebSocketManager {
    constructor(customerId, therapistId, jwtToken, userRole) {
        this.customerId = customerId;
        this.therapistId = therapistId;
        this.jwtToken = jwtToken;
        this.userRole = userRole;
        this.chatSocket = null;
        this.locationSocket = null;
    }

    connect() {
        this.connectChat();
        this.connectLocation();
    }

    connectChat() {
        const wsUrl = `ws://localhost:8000/ws/chat/${this.customerId}/${this.therapistId}/?token=${this.jwtToken}`;
        this.chatSocket = new WebSocket(wsUrl);

        this.chatSocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'message') {
                this.handleNewMessage(data);
            }
        };

        this.chatSocket.onopen = () => {
            console.log('Chat connected');
        };

        this.chatSocket.onclose = (event) => {
            console.log('Chat disconnected:', event.code);
            // Implement reconnection logic
        };
    }

    connectLocation() {
        const wsUrl = `ws://localhost:8000/ws/location/${this.customerId}/${this.therapistId}/?token=${this.jwtToken}`;
        this.locationSocket = new WebSocket(wsUrl);

        this.locationSocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'location') {
                this.handleLocationUpdate(data);
            }
        };

        this.locationSocket.onopen = () => {
            console.log('Location connected');
        };
    }

    sendMessage(message) {
        if (this.chatSocket && this.chatSocket.readyState === WebSocket.OPEN) {
            this.chatSocket.send(JSON.stringify({ message }));
        }
    }

    sendLocation(latitude, longitude) {
        if (this.userRole === 'therapist' && 
            this.locationSocket && 
            this.locationSocket.readyState === WebSocket.OPEN) {
            this.locationSocket.send(JSON.stringify({ latitude, longitude }));
        }
    }

    handleNewMessage(data) {
        // Implement your message handling logic
        console.log('New message:', data);
    }

    handleLocationUpdate(data) {
        // Implement your location update logic
        console.log('Location update:', data);
    }

    disconnect() {
        if (this.chatSocket) {
            this.chatSocket.close();
        }
        if (this.locationSocket) {
            this.locationSocket.close();
        }
    }
}

// Usage
const wsManager = new TherapyWebSocketManager(123, 456, 'your-jwt-token', 'customer');
wsManager.connect();

// Send a message
wsManager.sendMessage('Hello!');

// Send location (therapists only)
wsManager.sendLocation(40.7128, -74.0060);
```

## Security Considerations

1. **Authentication**: All connections require valid JWT tokens
2. **Authorization**: Users can only access conversations they're part of
3. **Role-based Actions**: Only therapists can send location updates
4. **Data Validation**: Empty messages are filtered out
5. **Error Handling**: Proper error logging and graceful connection handling

## Best Practices

1. **Reconnection Logic**: Implement automatic reconnection for network issues
2. **Message Queuing**: Queue messages when connection is temporarily lost
3. **Error Handling**: Handle all WebSocket error states gracefully
4. **Token Refresh**: Implement JWT token refresh before expiration
5. **Connection Cleanup**: Always close connections when leaving the chat/location view
6. **Rate Limiting**: Consider implementing client-side rate limiting for location updates