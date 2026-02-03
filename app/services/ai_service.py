import abc
import time
import logging

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

try:
    from transformers import AutoModelForCausalLM, AutoTokenizer
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

# Configure logging
logger = logging.getLogger(__name__)

class BaseAIService(abc.ABC):
    """Abstract base class for AI Services."""
    
    @abc.abstractmethod
    def generate_response(self, prompt: str, history: list = None) -> str:
        """Generate a response for the given prompt, optionally considering history."""
        pass

    @abc.abstractmethod
    def summarize_history(self, history: list) -> str:
        """Summarize the given conversation history."""
        pass

class MockAIService(BaseAIService):
    """Mock implementation for testing fallback scenarios."""
    
    def generate_response(self, prompt: str, history: list = None) -> str:
        time.sleep(1)  # Simulate inference latency
        history_len = len(history) if history else 0
        return f"""[MOCK RESPONSE - Qwen Model Not Loaded]
        
I received: "{prompt}" (Context: {history_len} previous messages)
"""

    def summarize_history(self, history: list) -> str:
        return f"[MOCK SUMMARY of {len(history)} messages]"

class QwenAIService(BaseAIService):
    """Real implementation using Qwen Coder model."""
    
    MODEL_NAME = "Qwen/Qwen2.5-Coder-3B-Instruct"

    def __init__(self):
        self._model = None
        self._tokenizer = None
        self._device = "cuda" if self._is_cuda_available() else "cpu"
        
        # Optimize: Enable TF32 if supported
        if self._device == "cuda" and HAS_TORCH:
            try:
                torch.backends.cuda.matmul.allow_tf32 = True
                logger.info("CUDA TF32 enabled.")
            except Exception as e:
                logger.warning(f"Failed to enable TF32: {e}")

    def _is_cuda_available(self):
        if not HAS_TORCH:
            return False
        return torch.cuda.is_available()

    def _load_model(self):
        """Loads the model and tokenizer. Called once at startup."""
        if self._model is not None:
            return

        if not HAS_TRANSFORMERS or not HAS_TORCH:
            raise ImportError("torch or transformers not installed.")

        logger.info(f"Loading Model {self.MODEL_NAME} on {self._device}...")
        try:
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
            raise e

    def summarize_history(self, history: list) -> str:
        """Summarizes the conversation history into a concise paragraph."""
        try:
            if self._model is None:
                self._load_model()
            
            # Construct a prompt for summarization
            history_text = ""
            for msg in history:
                role = "User" if msg["role"] == "user" else "Assistant"
                history_text += f"{role}: {msg['content']}\n\n"

            summary_prompt = f"""Summarize the following conversation history into one concise paragraph. 
Focus on the main coding task being discussed and any key decisions or requirements mentioned.
DO NOT write code in the summary.

CONVERSATION:
{history_text}

SUMMARY:"""

            messages = [
                {"role": "system", "content": "You are a concise summarization assistant."},
                {"role": "user", "content": summary_prompt}
            ]

            text = self._tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )

            model_inputs = self._tokenizer([text], return_tensors="pt").to(self._model.device)

            with torch.inference_mode():
                generated_ids = self._model.generate(
                    **model_inputs,
                    max_new_tokens=256,
                    temperature=0.3
                )

            generated_ids = [
                output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
            ]

            response = self._tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
            return response.strip()

        except Exception as e:
            logger.error(f"Summarization Error: {e}")
            return f"Failed to summarize: {str(e)}"

    def generate_response(self, prompt: str, history: list = None) -> str:
        try:
            if self._model is None:
                self._load_model()
            
            messages = [
                {"role": "system", "content": "You are Qwen, a helpful and comprehensive AI Coding Assistant. You can write code, debug, and explain concepts."}
            ]
            
            if history:
                formatted_history = []
                for msg in history[-20:]: 
                    role = "assistant" if msg["role"] == "ai" else "user"
                    formatted_history.append({"role": role, "content": msg["content"]})
                messages.extend(formatted_history)
            
            messages.append({"role": "user", "content": prompt})

            text = self._tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
            
            model_inputs = self._tokenizer([text], return_tensors="pt").to(self._model.device)
            
            with torch.inference_mode():
                generated_ids = self._model.generate(
                    **model_inputs,
                    max_new_tokens=1024,
                    temperature=0.2,
                    top_p=0.9
                )

            generated_ids = [
                output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
            ]
            
            return self._tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]

        except Exception as e:
            logger.error(f"LLM Generation Error: {e}")
            return f"Error regarding LLM: {str(e)}\n\n" + MockAIService().generate_response(prompt, history=history)


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
        if not HAS_TORCH or not HAS_TRANSFORMERS:
            raise ImportError("AI dependencies missing.")

        service = QwenAIService()
        service._load_model()
        
        _ai_service = service
        return _ai_service
        
    except (ImportError, Exception) as e:
        logger.warning(f"Failed to initialize QwenAIService ({e}). Using MockAIService.")
        _ai_service = MockAIService()
        return _ai_service
