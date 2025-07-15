import os
import cv2
import face_recognition
from concurrent.futures import ThreadPoolExecutor, as_completed

root_dir = "/home/marqs/Bilder/Lola_Myluv"
checkpoint_file = os.path.join(root_dir, ".processed_faces.txt")
valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp')
num_threads = os.cpu_count() or 4

# Läs tidigare bearbetade filer
def load_checkpoint():
    if not os.path.exists(checkpoint_file):
        return set()
    with open(checkpoint_file, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f)

def append_checkpoint(entry):
    with open(checkpoint_file, 'a', encoding='utf-8') as f:
        f.write(entry + "\n")

# Hitta alla bilder som inte redan behandlats
def find_all_images(root_folder, processed_set):
    file_list = []
    for dirpath, _, filenames in os.walk(root_folder):
        for filename in filenames:
            if filename.lower().endswith(valid_extensions):
                full_path = os.path.join(dirpath, filename)
                if full_path not in processed_set:
                    file_list.append(full_path)
    return file_list

def process_image(file_path):
    try:
        image = face_recognition.load_image_file(file_path)
        face_locations = face_recognition.face_locations(image)

        if len(face_locations) != 1:
            return f"⏭️ {file_path}: {len(face_locations)} ansikten hittades", False

        top, right, bottom, left = face_locations[0]
        face_image = image[top:bottom, left:right]
        face_image_resized = cv2.resize(face_image, (64, 64))

        base, _ = os.path.splitext(file_path)
        save_path = f"{base}_face.jpg"
        cv2.imwrite(save_path, cv2.cvtColor(face_image_resized, cv2.COLOR_RGB2BGR))

        return f"✅ Sparade: {save_path}", True

    except Exception as e:
        return f"❌ Fel i {file_path}: {e}", False

def main():
    processed_set = load_checkpoint()
    all_images = find_all_images(root_dir, processed_set)
    print(f"🔍 Hittade {len(all_images)} bilder att bearbeta")

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = {executor.submit(process_image, path): path for path in all_images}

        for future in as_completed(futures):
            result, success = future.result()
            print(result)
            if success:
                append_checkpoint(futures[future])

if __name__ == "__main__":
    main()
