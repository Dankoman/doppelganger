import os
import cv2
import face_recognition

# Basinställningar
root_dir = "/home/marqs/Bilder/pr0n"
output_dir = os.path.join(root_dir, "Faces")
checkpoint_file = os.path.join(root_dir, "processed_faces.txt")
valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp')
MIN_WIDTH = 150
MIN_HEIGHT = 150

# Läs tidigare bearbetade filer från checkpoint
def load_checkpoint():
    if not os.path.isfile(checkpoint_file):
        return set()
    with open(checkpoint_file, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f)

# Spara uppdaterad checkpoint
def save_checkpoint(processed):
    with open(checkpoint_file, 'w', encoding='utf-8') as f:
        for path in processed:
            f.write(path + '\n')

# Gå igenom alla bildfiler under root_dir
def find_image_files():
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.lower().endswith(valid_extensions):
                yield os.path.join(dirpath, filename)

# Extrahera ansikten och spara dem
def extract_and_save_faces(image_path):
    try:
        rel_dir = os.path.relpath(os.path.dirname(image_path), root_dir)
        person_dir = os.path.join(output_dir, rel_dir)
        os.makedirs(person_dir, exist_ok=True)

        image = cv2.imread(image_path)
        if image is None:
            return False

        if image.shape[1] < MIN_WIDTH or image.shape[0] < MIN_HEIGHT:
            return False

        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_image)

        for i, (top, right, bottom, left) in enumerate(face_locations):
            face_image = image[top:bottom, left:right]
            base_name = os.path.splitext(os.path.basename(image_path))[0]
            face_filename = f"{base_name}_face{i+1}.jpg"
            face_path = os.path.join(person_dir, face_filename)
            cv2.imwrite(face_path, face_image)

        return True

    except Exception as e:
        print(f"Fel vid behandling av {image_path}: {e}")
        return False

# Huvudkörning
def main():
    processed = load_checkpoint()
    images = [f for f in find_image_files() if f not in processed]

    print(f"🔍 Hittade {len(images)} bilder att bearbeta")

    for image_path in images:
        success = extract_and_save_faces(image_path)
        if success:
            processed.add(image_path)

    save_checkpoint(processed)
    print("✅ Klart.")

if __name__ == "__main__":
    main()
