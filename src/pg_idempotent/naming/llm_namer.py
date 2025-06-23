"""
Schema naming module using LLM and rule-based approaches.

This module provides intelligent schema naming suggestions using both
rule-based heuristics and LLM-powered naming when available.
"""

import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
import logging

logger = logging.getLogger(__name__)


@dataclass
class NamingContext:
    """Context for schema naming decisions."""
    
    sql_objects: List[Dict[str, any]]
    object_types: Dict[str, int]  # Type -> count mapping
    domain_hints: List[str] = field(default_factory=list)
    existing_names: Set[str] = field(default_factory=set)
    
    def __post_init__(self):
        """Validate context data."""
        if not self.sql_objects:
            self.sql_objects = []
        if not self.object_types:
            self.object_types = {}


class RuleBasedNamer:
    """Rule-based schema naming using heuristics."""
    
    # Common domain patterns and their schema suggestions
    DOMAIN_PATTERNS = {
        r'user|account|auth|login': 'auth',
        r'product|item|catalog|inventory': 'catalog',
        r'order|purchase|cart|checkout': 'commerce',
        r'payment|billing|invoice|subscription': 'billing',
        r'analytics|metric|event|tracking': 'analytics',
        r'audit|log|history': 'audit',
        r'config|setting|preference': 'config',
        r'notification|email|message|alert': 'messaging',
        r'media|image|video|file|upload': 'media',
        r'report|dashboard|visualization': 'reporting',
    }
    
    # Object type to schema mapping preferences
    TYPE_SCHEMA_HINTS = {
        'CREATE_FUNCTION': ['utils', 'helpers', 'procedures'],
        'CREATE_TRIGGER': ['triggers', 'automation'],
        'CREATE_VIEW': ['views', 'reporting'],
        'CREATE_TYPE': ['types', 'enums'],
    }
    
    def __init__(self):
        self.compiled_patterns = {
            pattern: re.compile(pattern, re.IGNORECASE)
            for pattern in self.DOMAIN_PATTERNS
        }
    
    def name_schemas(self, context: NamingContext) -> Dict[str, str]:
        """Generate schema names based on rules."""
        schema_assignments = {}
        schema_object_counts = {}
        
        # First pass: Analyze object names for domain hints
        domain_scores = self._analyze_domains(context)
        
        # Second pass: Assign objects to schemas
        for obj in context.sql_objects:
            obj_name = obj.get('name', '').lower()
            obj_type = obj.get('type', '')
            
            # Try domain-based assignment first
            schema = self._assign_by_domain(obj_name, domain_scores)
            
            # Fall back to type-based assignment
            if not schema and obj_type in self.TYPE_SCHEMA_HINTS:
                schema = self.TYPE_SCHEMA_HINTS[obj_type][0]
            
            # Default schema
            if not schema:
                schema = 'main'
            
            # Track assignments
            schema_assignments[obj_name] = schema
            schema_object_counts[schema] = schema_object_counts.get(schema, 0) + 1
        
        # Balance schemas if needed
        schema_assignments = self._balance_schemas(
            schema_assignments, schema_object_counts, context
        )
        
        return schema_assignments
    
    def _analyze_domains(self, context: NamingContext) -> Dict[str, float]:
        """Analyze objects to determine dominant domains."""
        domain_scores = {}
        
        # Score based on object names
        for obj in context.sql_objects:
            obj_name = obj.get('name', '').lower()
            
            for pattern, schema in self.DOMAIN_PATTERNS.items():
                if self.compiled_patterns[pattern].search(obj_name):
                    domain_scores[schema] = domain_scores.get(schema, 0) + 1
        
        # Normalize scores
        total = sum(domain_scores.values()) or 1
        return {k: v / total for k, v in domain_scores.items()}
    
    def _assign_by_domain(self, obj_name: str, domain_scores: Dict[str, float]) -> Optional[str]:
        """Assign object to schema based on domain matching."""
        best_match = None
        best_score = 0
        
        for pattern, schema in self.DOMAIN_PATTERNS.items():
            if self.compiled_patterns[pattern].search(obj_name):
                score = domain_scores.get(schema, 0)
                if score > best_score:
                    best_score = score
                    best_match = schema
        
        return best_match
    
    def _balance_schemas(
        self, 
        assignments: Dict[str, str], 
        counts: Dict[str, int],
        context: NamingContext
    ) -> Dict[str, str]:
        """Balance schema assignments to avoid overly large schemas."""
        MAX_OBJECTS_PER_SCHEMA = 20
        
        # Find overloaded schemas
        overloaded = {
            schema: count 
            for schema, count in counts.items() 
            if count > MAX_OBJECTS_PER_SCHEMA
        }
        
        if not overloaded:
            return assignments
        
        # Redistribute objects from overloaded schemas
        for schema in overloaded:
            objects_in_schema = [
                obj for obj, assigned_schema in assignments.items()
                if assigned_schema == schema
            ]
            
            # Split into sub-schemas
            chunk_size = MAX_OBJECTS_PER_SCHEMA
            for i in range(0, len(objects_in_schema), chunk_size):
                chunk = objects_in_schema[i:i + chunk_size]
                sub_schema = f"{schema}_{i // chunk_size + 1}" if i > 0 else schema
                
                for obj in chunk:
                    assignments[obj] = sub_schema
        
        return assignments


class LLMSchemaNamer:
    """LLM-powered schema naming using OpenAI API."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self._client = None
        
        if not self.api_key:
            logger.warning("No OpenAI API key found. LLM naming will be unavailable.")
    
    @property
    def client(self):
        """Lazy load OpenAI client."""
        if self._client is None and self.api_key:
            try:
                import openai
                self._client = openai.OpenAI(api_key=self.api_key)
            except ImportError:
                logger.error("OpenAI package not installed. Run: pip install openai")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
        return self._client
    
    def generate_schema_names(self, context: NamingContext) -> Dict[str, str]:
        """Generate schema names using LLM."""
        if not self.client:
            logger.warning("LLM client not available, falling back to empty result")
            return {}
        
        try:
            # Prepare context for LLM
            prompt = self._build_prompt(context)
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a PostgreSQL database architect specializing in schema organization."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            # Parse response
            return self._parse_llm_response(response.choices[0].message.content, context)
            
        except Exception as e:
            logger.error(f"LLM naming failed: {e}")
            return {}
    
    def _build_prompt(self, context: NamingContext) -> str:
        """Build prompt for LLM."""
        # Summarize objects
        object_summary = []
        for obj in context.sql_objects[:50]:  # Limit to avoid token limits
            object_summary.append(f"- {obj.get('type', 'UNKNOWN')}: {obj.get('name', 'unnamed')}")
        
        prompt = f"""Given the following PostgreSQL database objects, suggest appropriate schema names for logical organization.

Objects:
{chr(10).join(object_summary)}

Object type distribution:
{chr(10).join(f'- {t}: {c}' for t, c in context.object_types.items())}

Domain hints: {', '.join(context.domain_hints) if context.domain_hints else 'None provided'}

Requirements:
1. Create 2-6 schemas for logical separation
2. Use clear, descriptive schema names
3. Group related functionality together
4. Return a JSON mapping of object_name -> schema_name

Example output:
{{
  "user_table": "auth",
  "product_table": "catalog",
  "order_table": "commerce"
}}
"""
        return prompt
    
    def _parse_llm_response(self, response: str, context: NamingContext) -> Dict[str, str]:
        """Parse LLM response into schema assignments."""
        try:
            import json
            
            # Extract JSON from response
            json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
            if not json_match:
                logger.error("No JSON found in LLM response")
                return {}
            
            assignments = json.loads(json_match.group(0))
            
            # Validate assignments
            validated = {}
            for obj in context.sql_objects:
                obj_name = obj.get('name', '')
                if obj_name in assignments:
                    schema = assignments[obj_name]
                    # Basic validation
                    if isinstance(schema, str) and len(schema) < 64:
                        validated[obj_name] = schema
            
            return validated
            
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return {}


class SmartSchemaNamer:
    """Combines LLM and rule-based approaches for robust schema naming."""
    
    def __init__(self, api_key: Optional[str] = None, prefer_llm: bool = True):
        self.rule_namer = RuleBasedNamer()
        self.llm_namer = LLMSchemaNamer(api_key)
        self.prefer_llm = prefer_llm
    
    def generate_schema_names(self, context: NamingContext) -> Dict[str, str]:
        """Generate schema names using combined approach."""
        # Always get rule-based suggestions as fallback
        rule_based = self.rule_namer.name_schemas(context)
        
        # Try LLM if preferred and available
        if self.prefer_llm and self.llm_namer.api_key:
            llm_based = self.llm_namer.generate_schema_names(context)
            
            if llm_based:
                # Merge results, preferring LLM suggestions
                merged = rule_based.copy()
                merged.update(llm_based)
                return merged
        
        # Fall back to rule-based
        return rule_based
    
    def validate_schema_names(self, assignments: Dict[str, str]) -> Tuple[bool, List[str]]:
        """Validate schema name assignments."""
        errors = []
        
        # Check for empty assignments
        if not assignments:
            errors.append("No schema assignments provided")
            return False, errors
        
        # Validate schema names
        schema_pattern = re.compile(r'^[a-z][a-z0-9_]*$')
        for obj_name, schema in assignments.items():
            if not schema:
                errors.append(f"Empty schema name for object '{obj_name}'")
            elif not schema_pattern.match(schema):
                errors.append(f"Invalid schema name '{schema}' for object '{obj_name}'")
            elif len(schema) > 63:  # PostgreSQL limit
                errors.append(f"Schema name '{schema}' exceeds 63 character limit")
        
        # Check for reasonable schema count
        unique_schemas = set(assignments.values())
        if len(unique_schemas) > 20:
            errors.append(f"Too many schemas ({len(unique_schemas)}). Consider consolidation.")
        
        return len(errors) == 0, errors