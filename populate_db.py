import os
import django
import random
from faker import Faker
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import transaction
from io import BytesIO
from PIL import Image, ImageDraw

# 1. Setup Django
# CHANGE 'ecommerce.settings' to your actual project name if different
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings') 
django.setup()

from store.models import Category, Product
from taggit.models import Tag

# 2. Setup Fakers
fake_en = Faker('en_US')
fake_ar = Faker('ar_AA')

def create_single_placeholder_image():
    """Creates ONE image file to be shared by all products for performance."""
    img_name = 'placeholder_50k.jpg'
    path = f'product_images/{img_name}'
    
    if default_storage.exists(path):
        return path

    print("Generating single placeholder image...")
    img = Image.new('RGB', (200, 200), color=(50, 50, 50))
    d = ImageDraw.Draw(img)
    d.text((50, 90), "DEMO ITEM", fill=(255, 255, 255))
    
    buffer = BytesIO()
    img.save(buffer, format='JPEG')
    file = ContentFile(buffer.getvalue())
    
    return default_storage.save(path, file)

def populate():
    print("Starting SAFE population...")

    # ---------------------------------------------------------
    # 3. UPDATE OR CREATE CATEGORIES
    # ---------------------------------------------------------
    print("Updating/Creating Categories...")
    
    cat_data = {
        'Electronics': 'الكترونيات',
        'Clothing': 'ملابس',
        'Home': 'المنزل',
        'Books': 'كتب',
        'Sports': 'رياضة',
        'Beauty': 'تجميل',
        'Toys': 'ألعاب',
        'Automotive': 'سيارات',
        'Health': 'صحة',
        'Garden': 'حدائق',
        'Pets': 'حيوانات أليفة',
        'Jewelry': 'مجوهرات'
    }

    category_objects = []
    
    for en_name, ar_name in cat_data.items():
        # Robust Logic: Find by EN, then update AR if needed
        cat = Category.objects.filter(name_en=en_name).first()
        
        if not cat:
            # Check by AR just in case
            cat = Category.objects.filter(name_ar=ar_name).first()

        if cat:
            # Update existing if translation missing
            if not cat.name_ar:
                cat.name_ar = ar_name
                cat.save()
        else:
            # Create new
            cat = Category.objects.create(name_en=en_name, name_ar=ar_name)
            
        category_objects.append(cat)
    
    print(f"Categories ready: {len(category_objects)}")

    # ---------------------------------------------------------
    # 4. UPDATE OR CREATE TAGS (FIXED CRASH LOGIC)
    # ---------------------------------------------------------
    print("Updating/Creating Tags...")

    tag_data = {
        'New': 'جديد',
        'Sale': 'تخفيض',
        'Hot': 'رائج',
        'Tech': 'تقنية',
        'Deal': 'صفقة',
        'Premium': 'فاخر',
        'Limited': 'محدود',
        'Exclusive': 'حصري',
        'Eco': 'بيئي',
        'Gift': 'هدية'
    }

    tag_objects = []

    for en_name, ar_name in tag_data.items():
        # 1. Try finding by English Name
        tag = Tag.objects.filter(name_en=en_name).first()
        
        # 2. If not found, try finding by Arabic Name
        if not tag:
            tag = Tag.objects.filter(name_ar=ar_name).first()

        # 3. Logic to Update or Create
        if tag:
            # Found existing tag (by EN or AR). Update missing fields.
            save_needed = False
            
            # Ensure English name matches what we expect
            if tag.name_en != en_name:
                tag.name_en = en_name
                save_needed = True
                
            # Ensure Arabic name matches
            if tag.name_ar != ar_name:
                tag.name_ar = ar_name
                save_needed = True
            
            if save_needed:
                tag.save()
        else:
            # Tag doesn't exist in either language -> Create new
            tag = Tag.objects.create(name_en=en_name, name_ar=ar_name)
            
        tag_objects.append(tag)

    print(f"Tags ready: {len(tag_objects)}")

    # ---------------------------------------------------------
    # 5. PREPARE PRODUCT DATA
    # ---------------------------------------------------------
    image_path = create_single_placeholder_image()
    
    keyword_map = {
        'Galaxy': 'جالكسي', 'Smart': 'ذكي', 'Pro': 'برو', 
        'Super': 'سوبر', 'Modern': 'عصري', 'Ultra': 'ألترا',
        'Mega': 'ميغا', 'Prime': 'برايم', 'Elite': 'نخبة'
    }
    keys = list(keyword_map.keys())

    total_products = 50000 
    print(f"Adding {total_products} NEW products...")

    # ---------------------------------------------------------
    # 6. MAIN LOOP (Atomic Transaction)
    # ---------------------------------------------------------
    try:
        with transaction.atomic():
            for i in range(total_products):
                category = random.choice(category_objects)
                key_en = random.choice(keys)
                key_ar = keyword_map[key_en]
                
                # Large offset to prevent duplicate slug collisions with old data
                unique_id = i + 300000 

                # Generate English
                if random.random() < 0.6:
                    name_en = f"{key_en} {fake_en.word().title()} {unique_id}"
                else:
                    name_en = f"{fake_en.word().title()} {key_en} {unique_id}"
                desc_en = f"This is a great {key_en} product. {fake_en.text(max_nb_chars=100)}"

                # Generate Arabic
                if random.random() < 0.6:
                    name_ar = f"{key_ar} {fake_ar.word()} {unique_id}"
                else:
                    name_ar = f"{fake_ar.word()} {key_ar} {unique_id}"
                desc_ar = f"هذا منتج {key_ar} رائع جدا. {fake_ar.text(max_nb_chars=100)}"

                # Create Product
                product = Product(
                    category=category,
                    name_en=name_en,
                    name_ar=name_ar,
                    description_en=desc_en,
                    description_ar=desc_ar,
                    price=round(random.uniform(10, 2000), 2),
                    stock=random.randint(0, 500),
                    is_avaliable=True,
                    is_active=True
                )
                
                product.image.name = image_path
                product.save()

                # Add Tags (Pick 1 random tag from our verified bilingual list)
                if random.random() < 0.3:
                    t = random.choice(tag_objects)
                    product.tags.add(t)

                if (i + 1) % 5000 == 0:
                    print(f"Added {i + 1}/{total_products} products...")

    except Exception as e:
        print(f"Error occurred: {e}")
    
    print("Done! Categories and Tags updated, Products added.")

if __name__ == '__main__':
    populate()