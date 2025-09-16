import cv2
import numpy as np
import pickle
import os

def encode_faces():
    """Generate face encodings for all images in dataset folder using OpenCV"""
    known_faces = []
    known_names = []
    label_ids = {}
    current_label = 0
    
    # Load face detection model
    face_detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    # Load face recognition model
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    
    # Loop through each person's directory in dataset
    for person_id in os.listdir("dataset"):
        person_dir = os.path.join("dataset", person_id)
        if os.path.isdir(person_dir):
            # Assign numeric label for this person
            if person_id not in label_ids:
                label_ids[person_id] = current_label
                current_label += 1
                
            faces = []
            labels = []
            
            # Process each image
            for image_name in os.listdir(person_dir):
                image_path = os.path.join(person_dir, image_name)
                
                try:
                    image = cv2.imread(image_path)
                    if image is None:
                        print(f"Could not read {image_path}")
                        continue
                        
                    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                    detected_faces = face_detector.detectMultiScale(gray, 1.3, 5)
                    
                    if len(detected_faces) > 0:
                        (x, y, w, h) = detected_faces[0]
                        face_img = cv2.resize(gray[y:y+h, x:x+w], (200, 200))
                        faces.append(face_img)
                        labels.append(label_ids[person_id])
                        print(f"Processed {image_path}")
                    else:
                        print(f"No face found in {image_path}")
                except Exception as e:
                    print(f"Error processing {image_path}: {str(e)}")
            
            if faces:
                known_faces.extend(faces)
                known_names.extend([person_id] * len(faces))
    
    if known_faces and known_names:
        try:
            # Convert lists to numpy arrays
            faces_array = np.array(known_faces)
            labels_array = np.array(labels)
            
            # Train recognizer
            recognizer.train(faces_array, labels_array)
            
            # Save model
            recognizer.write("face_model.yml")
            
            # Save label mapping
            data = {
                "names": known_names,
                "label_ids": label_ids
            }
            with open("encodings.pickle", "wb") as f:
                pickle.dump(data, f)
            
            print("Encoding completed and saved successfully")
            print(f"Total faces encoded: {len(faces_array)}")
            print(f"Total people: {len(label_ids)}")
        except Exception as e:
            print(f"Error during training: {str(e)}")
    else:
        print("No faces found in dataset!")

if __name__ == "__main__":
    encode_faces()
