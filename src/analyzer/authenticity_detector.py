import os
import re
from typing import Dict, List, Set

class AuthenticityDetector:
    """Detects and scores AI implementation authenticity"""
    
    KNOWN_AI_FRAMEWORKS = {
        'tensorflow': {
            'imports': {r'import\s+tensorflow', r'import\s+tf', r'from\s+tensorflow'},
            'basic_patterns': {
                r'model\s*=\s*tf',  # Match simple model assignments
                r'keras\.Sequential',  # Match both tf.keras and plain keras
                r'keras\.layers',
                r'keras\.Model',
                r'tf\.keras',  # General tf.keras usage
                r'Sequential\s*\(\s*\)'  # Match bare Sequential constructor
            },
            'advanced_patterns': {
                r'class\s+\w+\s*\(\s*tf\.keras\.Model\s*\)',
                r'tf\.GradientTape',
                r'@tf\.function',
                r'custom_training_loop',
                r'tf\.data\.Dataset'
            },
            'weight': 1.0  # Full framework implementation
        },
        'pytorch': {
            'imports': {r'import\s+torch', r'from\s+torch', r'import\s+torch\.nn'},
            'basic_patterns': {
                r'torch\.nn',  # Match any torch.nn usage
                r'nn\.',  # Match imported nn usage
                r'torch\.optim',
                r'model\.forward',
                r'torch\.utils\.data',
                r'Module\s*\(',  # Match both nn.Module and torch.nn.Module
                r'Linear\s*\('  # Match both nn.Linear and torch.nn.Linear
            },
            'advanced_patterns': {
                r'class\s+\w+\s*\(\s*nn\.Module\s*\)',
                r'torch\.autograd',
                r'@torch\.jit\.script',
                r'custom_loss',
                r'torch\.cuda'
            },
            'weight': 1.0  # Full framework implementation
        },
        'transformers': {
            'imports': {r'from\s+transformers', r'import\s+transformers'},
            'basic_patterns': {
                r'AutoModel\s*\.',
                r'AutoTokenizer\s*\.',
                r'pipeline\s*\(',
                r'from_pretrained\s*\(',
                r'PreTrainedModel\s*\(',
                r'transformers\.'
            },
            'advanced_patterns': {
                r'class\s+\w+\s*\(\s*PreTrainedModel\s*\)',
                r'custom_head',
                r'trainer\.train',
                r'model\.train',
                r'custom_tokens'
            },
            'weight': 0.9  # High-level but still framework
        },
        'openai': {
            'imports': {r'import\s+openai', r'from\s+openai', r'OpenAI', r'import\s*{\s*Configuration,\s*OpenAIApi\s*}'},
            'basic_patterns': {
                r'openai\.Completion\.create', r'openai\.ChatCompletion\.create', 
                r'new\s+OpenAI\s*\(\s*\)', r'OpenAIApi', r'gpt-4', r'gpt-3\.5-turbo',
                r'createChatCompletion', r'createCompletion'
            },
            'advanced_patterns': {
                r'fine_tuning',
                r'custom_prompts',
                r'system_messages',
                r'context_window',
                r'token_handling'
            },
            'weight': 0.5  # API-level usage
        },
        'langchain': {
            'imports': {r'from\s+langchain', r'import\s+langchain', r'import\s*{\s*LangChain\s*}'},
            'basic_patterns': {
                r'LLMChain', r'PromptTemplate', r'ChatPromptTemplate',
                r'VectorStore', r'Embeddings', r'BaseLanguageModel'
            },
            'advanced_patterns': {
                r'custom_chain',
                r'custom_agent',
                r'custom_tool',
                r'memory_implementation',
                r'custom_retriever'
            },
            'weight': 0.7  # Framework with some abstraction
        },
        'rig': {
            'imports': {'use rig', 'from rig'},
            'basic_patterns': {
                r'CompletionModel', r'EmbeddingModel', r'Agent',
                r'VectorStore'
            },
            'advanced_patterns': {
                r'custom_provider',
                r'custom_model',
                r'custom_agent',
                r'custom_store',
                r'custom_embedding'
            },
            'weight': 0.8  # Framework with low-level access
        }
    }
    
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        
    async def analyze_authenticity(self) -> float:
        """
        Analyze AI implementation authenticity
        Returns a score between 0 and 1, where:
        1.0: Deep framework implementation (custom models, training)
        0.8: Framework usage with custom components
        0.5: Basic API usage
        0.0: No AI implementation
        """
        self.framework_scores = {}
        detected = self._find_framework_implementations()
        if not detected:
            return 0.0
            
        # Calculate base score from implementation quality
        implementation_score = self._analyze_implementation(detected)
        
        # Calculate framework coverage score
        framework_scores = list(self.framework_scores.values())
        if not framework_scores:
            return 0.0
            
        avg_framework_score = sum(framework_scores) / len(framework_scores)
        
        # Combine implementation and framework scores
        final_score = (implementation_score + avg_framework_score) / 2
        
        return min(1.0, final_score)
        
    def _find_framework_implementations(self) -> Set[str]:
        """Find AI framework implementations in the codebase"""
        detected_frameworks = set()
        framework_scores = {}
        
        for root, _, files in os.walk(self.repo_path):
            for file in files:
                if not file.endswith(('.py', '.rs', '.ts', '.tsx', '.js', '.jsx')):  # Support Python, Rust, and TypeScript/JavaScript
                    continue
                    
                with open(os.path.join(root, file), 'r') as f:
                    content = f.read()
                    
                for framework, patterns in self.KNOWN_AI_FRAMEWORKS.items():
                    score = 0
                    # Check imports (20% of framework score)
                    if any(re.search(pattern, content, re.MULTILINE | re.IGNORECASE) for pattern in patterns['imports']):
                        score += 0.2
                        
                    # Check basic implementation patterns (30% of framework score)
                    basic_matches = sum(1 for pattern in patterns['basic_patterns']
                                     if re.search(pattern, content, re.MULTILINE | re.IGNORECASE))
                    if basic_matches > 0:
                        score += min(0.3, basic_matches * 0.1)  # Cap at 0.3
                        
                    # Check advanced implementation patterns (50% of framework score)
                    advanced_matches = sum(1 for pattern in patterns['advanced_patterns']
                                       if re.search(pattern, content, re.MULTILINE | re.IGNORECASE))
                    if advanced_matches > 0:
                        score += min(0.5, advanced_matches * 0.1)  # Cap at 0.5
                        
                    # Apply framework weight
                    score *= patterns['weight']
                    
                    # Update framework score if higher than existing
                    if score > 0:
                        framework_scores[framework] = max(
                            score,
                            framework_scores.get(framework, 0)
                        )
                        # More lenient detection for test files and imports
                        if any(re.search(pattern, content, re.MULTILINE | re.IGNORECASE) for pattern in patterns['imports']):
                            detected_frameworks.add(framework)  # Add framework if imports are found
                        elif score > 0.2:  # Add if significant implementation found
                            detected_frameworks.add(framework)
        
        # Update instance variable for use in scoring
        self.framework_scores = framework_scores
        return detected_frameworks
        
    def _analyze_implementation(self, frameworks: Set[str]) -> float:
        """
        Analyze implementation depth of AI frameworks
        Returns a score between 0 and 1, where:
        1.0: Deep framework implementation (custom models, training)
        0.8: Framework usage with custom components
        0.5: Basic API usage
        0.0: No implementation
        
        Multiple framework bonus:
        - 2 frameworks: +20% bonus
        - 3+ frameworks: +40% bonus
        """
        if not frameworks:
            return 0.0
            
        # Calculate base score from framework weights
        total_weight = sum(self.KNOWN_AI_FRAMEWORKS[f]['weight'] for f in frameworks)
        base_score = total_weight / len(frameworks)
        
        # Apply multiple framework bonus
        if len(frameworks) >= 3:
            base_score *= 1.4  # 40% bonus for 3+ frameworks
        elif len(frameworks) == 2:
            base_score *= 1.2  # 20% bonus for 2 frameworks
            
        return min(1.0, base_score)
        
        # Bonus for multiple framework integration
        if len(frameworks) > 1:
            base_score *= (1.0 + 0.1 * (len(frameworks) - 1))  # 10% bonus per additional framework
            
        return min(1.0, base_score)  # Cap at 1.0
