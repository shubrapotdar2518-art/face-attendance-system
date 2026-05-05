import cv2

print("Testing camera...")

# Try camera index 0
camera = cv2.VideoCapture(0)

if camera.isOpened():
    print("✓ Camera 0 opened successfully!")
    
    # Try to read a frame
    ret, frame = camera.read()
    
    if ret:
        print("✓ Frame captured successfully!")
        print(f"Frame size: {frame.shape}")
    else:
        print("✗ Could not capture frame")
    
    camera.release()
else:
    print("✗ Camera 0 failed to open")
    print("\nTrying camera index 1...")
    
    # Try camera index 1
    camera = cv2.VideoCapture(1)
    if camera.isOpened():
        print("✓ Camera 1 opened successfully!")
        camera.release()
    else:
        print("✗ Camera 1 also failed")

print("\nTest complete")