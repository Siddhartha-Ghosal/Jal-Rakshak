import os
from PIL import Image

def generate_images():
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
    os.makedirs(static_dir, exist_ok=True)
    
    # 1. Algae Sample (Greenish)
    img_algae = Image.new("RGB", (300, 300), color=(46, 125, 50))
    img_algae.save(os.path.join(static_dir, "sample_algae.jpg"))
    print(f"Generated sample_algae.jpg in {static_dir}")
    
    # 2. Discoloration Sample (Brownish/Muddy)
    img_muddy = Image.new("RGB", (300, 300), color=(141, 110, 99))
    img_muddy.save(os.path.join(static_dir, "sample_discoloration.jpg"))
    print(f"Generated sample_discoloration.jpg in {static_dir}")
    
    # 3. Clear Sample (Bluish/Clear)
    img_clear = Image.new("RGB", (300, 300), color=(135, 206, 235))
    img_clear.save(os.path.join(static_dir, "sample_clear.jpg"))
    print(f"Generated sample_clear.jpg in {static_dir}")

if __name__ == "__main__":
    generate_images()
