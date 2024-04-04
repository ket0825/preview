from paddleocr import PaddleOCR

class OCREngine:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls._instance = PaddleOCR(lang="korean")
        return cls._instance