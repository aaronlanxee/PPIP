import socketio
from PySide6.QtCore import QObject, Signal, QThread

class SocketClient(QObject):
    """
    WebSocket client for real-time notifications.
    Emits signals when notifications are received.
    """
    
    # Signals
    pet_missing_signal = Signal(dict)  # Emitted when a pet is marked as missing
    pet_found_signal = Signal(dict)  # Emitted when a pet is found
    connected_signal = Signal()  # Emitted when connected to server
    disconnected_signal = Signal()  # Emitted when disconnected
    
    def __init__(self, backend_url="http://127.0.0.1:5000"):
        super().__init__()
        self.sio = socketio.Client()
        self.backend_url = backend_url
        self.connected = False
        self.user_id = None
        
        # Register event handlers
        self.sio.on('connect', self.on_connect)
        self.sio.on('disconnect', self.on_disconnect)
        self.sio.on('pet_missing', self.on_pet_missing)
        self.sio.on('pet_found', self.on_pet_found)
    
    def on_connect(self):
        """Called when connected to WebSocket server"""
        print("✓ Connected to WebSocket server")
        self.connected = True
        # Join user-specific room if user_id is set
        if self.user_id:
            self.sio.emit('join_room', {'room': f'user_{self.user_id}'})
        self.connected_signal.emit()
    
    def on_disconnect(self):
        """Called when disconnected from WebSocket server"""
        print("✗ Disconnected from WebSocket server")
        self.connected = False
        self.disconnected_signal.emit()
    
    def on_pet_missing(self, data):
        """Called when a pet missing notification is received"""
        print(f"🔔 Received pet missing notification: {data}")
        self.pet_missing_signal.emit(data)
    
    def on_pet_found(self, data):
        """Called when a pet found notification is received"""
        print(f"🎉 Received pet found notification: {data}")
        self.pet_found_signal.emit(data)
    
    def connect(self, user_id=None):
        """Connect to the WebSocket server"""
        try:
            self.user_id = user_id
            if not self.connected:
                self.sio.connect(self.backend_url, transports=['websocket', 'polling'])
                # Join user room after connection
                if user_id:
                    self.sio.emit('join_room', {'room': f'user_{user_id}'})
                return True
        except Exception as e:
            print(f"Error connecting to WebSocket: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from the WebSocket server"""
        try:
            if self.connected:
                self.sio.disconnect()
        except Exception as e:
            print(f"Error disconnecting from WebSocket: {e}")
    
    def is_connected(self):
        """Check if connected to the server"""
        return self.connected
