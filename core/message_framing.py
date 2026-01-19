import struct


class MessageFraming:
    MAX_MESSAGE_SIZE = 10 * 1024 * 1024  # 10MB limit

    @staticmethod
    def frame_message(message: str) -> bytes:
        encoded = message.encode('utf-8')
        if len(encoded) > MessageFraming.MAX_MESSAGE_SIZE:
            raise ValueError("Message size exceeds maximum allowed size")
        length_prefix = struct.pack('>I', len(encoded))
        return length_prefix + encoded
    
    @staticmethod
    def extract_message(data: bytes) -> tuple[str, int]:
        if len(data) < 4:
            return "", 0
        
        length = struct.unpack('>I', data[:4])[0]
        
        if length > MessageFraming.MAX_MESSAGE_SIZE:
            raise ValueError("Message length exceeds maximum allowed size")
        
        if len(data) < 4 + length:
            return "", 0
        
        message = data[4:4 + length].decode('utf-8')
        return message, 4 + length
    
    @staticmethod
    def has_complete_message(data: bytes) -> bool:
        if len(data) < 4:
            return False
        
        length = struct.unpack('>I', data[:4])[0]
        
        if length > MessageFraming.MAX_MESSAGE_SIZE:
            return False
        
        return len(data) >= 4 + length
