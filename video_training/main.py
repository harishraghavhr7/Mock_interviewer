import os
import cv2
from mtcnn import MTCNN

# Input dataset
INPUT_DIR = "DATASETS"

# Output dataset
OUTPUT_DIR = "faces"

# Initialize detector
detector = MTCNN()

# Labels
labels = ["confident", "non_confident"]

for label in labels:

    input_folder = os.path.join(INPUT_DIR, label)
    output_folder = os.path.join(OUTPUT_DIR, label)

    os.makedirs(output_folder, exist_ok=True)

    for img_name in os.listdir(input_folder):

        img_path = os.path.join(input_folder, img_name)

        image = cv2.imread(img_path)

        if image is None:
            continue

        # Convert BGR to RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Detect faces
        faces = detector.detect_faces(rgb_image)

        if len(faces) == 0:
            continue

        # Take largest face
        largest_face = max(
            faces,
            key=lambda x: x['box'][2] * x['box'][3]
        )

        x, y, w, h = largest_face['box']

        # Prevent negative coordinates
        x = max(0, x)
        y = max(0, y)

        face_crop = image[y:y+h, x:x+w]

        # Resize
        face_crop = cv2.resize(face_crop, (224, 224))

        save_path = os.path.join(output_folder, img_name)

        cv2.imwrite(save_path, face_crop)

        print(f"Saved: {save_path}")

print("Face extraction completed.")