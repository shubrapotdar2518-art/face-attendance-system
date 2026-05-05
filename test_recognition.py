import cv2
import os

# Paths
registered_photo = 'data/faces/EMP001_xxxxx.jpg'  # Change to your actual file
test_photo = 'test_snapshot.jpg'  # We'll create this

# Take a snapshot from webcam
camera = cv2.VideoCapture(0)
ret, frame = camera.read()
if ret:
    cv2.imwrite(test_photo, frame)
    print(f"✓ Snapshot saved: {test_photo}")
camera.release()

# Compare
img1 = cv2.imread(registered_photo, cv2.IMREAD_GRAYSCALE)
img2 = cv2.imread(test_photo, cv2.IMREAD_GRAYSCALE)

img1 = cv2.resize(img1, (100, 100))
img2 = cv2.resize(img2, (100, 100))

hist1 = cv2.calcHist([img1], [0], None, [256], [0, 256])
hist2 = cv2.calcHist([img2], [0], None, [256], [0, 256])

cv2.normalize(hist1, hist1, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
cv2.normalize(hist2, hist2, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)

similarity = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)

print(f"\nSimilarity score: {similarity:.3f}")
print(f"Recognition: {'✓ MATCH' if similarity > 0.3 else '✗ NO MATCH'}")