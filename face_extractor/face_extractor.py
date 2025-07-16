import os
import cv2
import face_recognition

# Basinställningar
root_dir = "/home/marqs/Bilder/pr0n"
checkpoint_file = os.path.join(root_dir, ".processed_faces.txt")
valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp')
MIN_WIDTH = 150
MIN_HEIGHT = 150

# Läs tidigare bearbetade filer från checkpoint
def load_checkpoint():
    if not os.path.exists(checkpoint_file):
        return set()
    with open(checkpoint_file, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f)

# Lägg till fil i checkpoint
def append_checkpoint(entry):
    with open(checkpoint_file, 'a', encoding='utf-8') as f:
        f.write(entry + "\n")

# Hitta bilder som inte redan behandlats
def find_all_images(root_folder, processed_set):
    file_list = []
    for dirpath, _, filenames in os.walk(root_folder):
        for filename in filenames:
            if filename.lower().endswith(valid_extensions):
                full_path = os.path.join(dirpath, filename)
                if full_path not in processed_set:
                    file_list.append(full_path)
    return file_list

# Bearbeta en bild
def process_image(file_path):
    try:
        image = face_recognition.load_image_file(file_path)

        height, width = image.shape[:2]
        if width < MIN_WIDTH or height < MIN_HEIGHT:
            return f"⏭️ {file_path}: Bilden är för liten ({width}x{height})", False

        face_locations = face_recognition.face_locations(image)
        if len(face_locations) != 1:
            return f"⏭️ {file_path}: {len(face_locations)} ansikten hittades", False

        top, right, bottom, left = face_locations[0]
        face_image = image[top:bottom, left:right]
        face_image_resized = cv2.resize(face_image, (128, 128))

        base, _ = os.path.splitext(file_path)
        save_path = f"{base}_face.jpg"
        cv2.imwrite(save_path, cv2.cvtColor(face_image_resized, cv2.COLOR_RGB2BGR))

        return f"✅ Sparade: {save_path}", True

    except Exception as e:
        return f"❌ Fel i {file_path}: {e}", False

# Huvudfunktion utan trådar
def main():
    processed_set = load_checkpoint()
    all_images = find_all_images(root_dir, processed_set)
    print(f"🔍 Hittade {len(all_images)} bilder att bearbeta")

    for path in all_images:
        result, success = process_image(path)
        print(result)
        if success:
            append_checkpoint(path)

if __name__ == "__main__":
    main()
