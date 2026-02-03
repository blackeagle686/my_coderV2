import abc
import time
import logging

# Configure logging
logger = logging.getLogger(__name__)

class BaseAIService(abc.ABC):
    """Abstract base class for AI Services."""
    
    @abc.abstractmethod
    def generate_response(self, prompt: str) -> str:
        """Generate a response for the given prompt."""
        pass

class MockAIService(BaseAIService):
    """Mock implementation for testing fallback scenarios."""
    
    def generate_response(self, prompt: str) -> str:
        time.sleep(1) # Simulate inference latency
        return f"""[MOCK RESPONSE - Qwen Model Not Loaded]
        
I received: "{prompt}"

Since `torch` or `transformers` are not installed or the model failed to load in this environment, I am responding with this mock message.

To use the real model, ensure dependencies are installed and you have a GPU:
`pip install torch transformers accelerate`

Here is a sample code snippet:
```python
def mock_code():
    print("Real AI generation unavailable.")
```
"""

# ... [Imports and Base Classes remain the same] ...

    def __init__(self):
        self._model = None
        self._tokenizer = None
        self._device = "cuda" if self._is_cuda_available() else "cpu"
        
        # Optimize: Enable TF32 if supported
        if self._device == "cuda":
            try:
                import torch
                torch.backends.cuda.matmul.allow_tf32 = True
                logger.info("CUDA TF32 enabled.")
            except Exception:
                pass

    def _is_cuda_available(self):
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False

    def _load_model(self):
        """Loads the model and tokenizer. Called once at startup."""
        if self._model is not None:
            return

        logger.info(f"Loading Model {self.MODEL_NAME} on {self._device}...")
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer

            self._tokenizer = AutoTokenizer.from_pretrained(self.MODEL_NAME)
            
            # Load model with optimizations
            dtype = torch.float16 if self._device == "cuda" else torch.float32
            self._model = AutoModelForCausalLM.from_pretrained(
                self.MODEL_NAME,
                torch_dtype=dtype,
                device_map="auto"
            )
            
            # Warm-up the model to remove cold-start latency
            logger.info("Warming up model...")
            self.generate_response("Hello")
            logger.info("Model loaded and warmed up successfully.")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            # If loading fails here, we might want to let the caller handle it or fallback
            raise e

    def generate_response(self, prompt: str) -> str:
        try:
            if self._model is None:
                # Should have been loaded at startup, but just in case
                self._load_model()
            
            import torch
            
            messages = [
                {"role": "system", "content": "You are Qwen, a helpful and comprehensive AI Coding Assistant. You can write code, debug, and explain concepts."},
                {"role": "user", "content": prompt}
            ]
            
            text = self._tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
            
            model_inputs = self._tokenizer([text], return_tensors="pt").to(self._model.device)
            
            # OPtimization: Use inference_mode
            with torch.inference_mode():
                generated_ids = self._model.generate(
                    **model_inputs,
                    max_new_tokens=512, # Reduced from 1024
                    temperature=0.2,
                    top_p=0.9
                )
            
            generated_ids = [
                output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
            ]
            
            response = self._tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
            return response

        except Exception as e:
            logger.error(f"LLM Generation Error: {e}")
            return f"Error regarding LLM: {str(e)}\n\n" + MockAIService().generate_response(prompt)

# Singleton Instance
_ai_service = None

def get_ai_service() -> BaseAIService:
    """
    Factory function to return the singleton AI service.
    Loads the model if not already loaded.
    """
    global _ai_service
    
    if _ai_service is not None:
        return _ai_service

    try:
        import torch
        import transformers
        
        service = QwenAIService()
        # Explicitly load model on creation (Startup)
        service._load_model()
        
        _ai_service = service
        return _ai_service
        
    except (ImportError, Exception) as e:
        logger.warning(f"Failed to initialize QwenAIService ({e}). Using MockAIService.")
        _ai_service = MockAIService()
        return _ai_service

# Export a function to get it, rather than the instance directly, 
# though main.py can call this at startup.

