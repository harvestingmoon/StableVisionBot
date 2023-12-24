from diffusers import StableDiffusionPipeline, EulerDiscreteScheduler, StableDiffusionImg2ImgPipeline, DDIMScheduler
import torch
import io
from PIL import Image

''' Class to hold storage stuff'''
class BackEnd:
    def __init__(self,model_id) -> None:
        self.model = None
        self.curr_picture = None 
        self.final_img = None
        self.call = {1:False,2:False}
        self.model_id = (model_id if model_id else "stabilityai/stable-diffusion-2")
    def change_picture(self,array): # picture received from user is a byte array  need to convert into image 
        picture = io.BytesIO(array)
        image = Image.open(picture).convert("RGB")
        self.curr_picture = image # store it temp 
    def final_(self,img):
        self.final_img = img
    def get_final(self):
        return self.final_img
    def get_picture(self):
         return self.curr_picture
    def change_model(self,model):
        self.model = model
    def get_model(self):
         return self.model
    def get_call(self):
         return self.call
    def call_engine(self,type):
        model_id = self.model_id
        call = self.get_call()
        device = ("cuda" if torch.cuda.is_available() else "cpu")
        if not call[type]:
            if True in list(call.values()):
                for k,v in call.items():
                    if v == True:
                        call[k] = False
            if type == 1:
                scheduler = DDIMScheduler.from_pretrained(model_id,subfolder = "scheduler")
                pipe = StableDiffusionPipeline.from_pretrained(model_id,scheduler= scheduler, torch_dtype = torch.float16)
            else:
                pipe = StableDiffusionImg2ImgPipeline.from_pretrained(model_id,torch_dtype = torch.float16)
            pipe = pipe.to(device)
            self.model = pipe
            call[type] = True
        return self.get_model()


''' Post processing of images'''
def post_process(image,to_doc = True):
    def resize_image(image, max_size):
        quality = 95
        while True:
            with io.BytesIO() as file:
                image.save(file, format='JPEG', quality=quality)
                size = file.tell() / 1024  # Size in KB
            if size <= max_size:
                break
            quality -= 5  # Decrease quality by 5. You can change it as needed.
            if quality < 0:
                raise Exception("Cannot reduce image size under the limit without losing too much quality.")
        return image
    
    def enforce_ratio(image,max_ratio): # stick to 20; 1
        width, height = image.size
        ratio = width / height

        if ratio > max_ratio:
            new_width = height * max_ratio
            image = image.resize((int(new_width), height), Image.ANTIALIAS)
        elif ratio < 1 / max_ratio:
            new_height = width * max_ratio
            image = image.resize((width, int(new_height)), Image.ANTIALIAS)

        return image

    def limit_pixels(image, max_pixels):
        width, height = image.size
        current_pixels = width * height

        if current_pixels > max_pixels:
            # Calculate the scale factor
            scale_factor = (max_pixels / current_pixels) ** 0.5
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            image = image.resize((new_width, new_height), Image.ANTIALIAS)

        return image

    def pil_to_file(image):
        file = io.BytesIO()
        if to_doc:
            image.save(file, format='PDF')
        else:
            image.save(file,format = 'JPG')
        file.seek(0)
        return file
    if not to_doc:
      image = resize_image(image, 9 * 1024)
      image = enforce_ratio(image,18)
      image = limit_pixels(image, 8000)
    image = pil_to_file(image)
    return image