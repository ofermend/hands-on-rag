"""
Graph Query Generator for Movie Knowledge Graph

This module provides a unified interface for generating and executing Cypher queries
from natural language questions using an LLM. It includes self-correction capabilities
and comprehensive error handling.

Usage:
    from graph_query_generator import GraphQueryGenerator, GRAPH_SCHEMA

    generator = GraphQueryGenerator(uri, user, password)
    results = generator.query_with_chunks("What movies did Pierce Brosnan act in?")
    generator.close()
"""

import os
from typing import List, Dict, Any, Optional, Tuple
from neo4j import GraphDatabase
from openai import OpenAI
from pydantic import BaseModel


# Graph Schema Definition
GRAPH_SCHEMA = """
## Movie Knowledge Graph Schema

### Nodes:
1. **Movie**
   - Properties: imdb_id, title, original_title, start_year, runtime_minutes, genres (list)
   - Example: {title: "Inception", start_year: 2010}

2. **Person**
   - Properties: imdb_id, name, birth_year, death_year, professions (list)
   - Example: {name: "christopher nolan", professions: ["director", "writer"]}

3. **Genre**
   - Properties: name
   - Example: {name: "sci-fi"}

4. **Character**
   - Properties: name, source
   - Example: {name: "dom cobb"}
   - Note: Character nodes are extracted from movie scripts, not from IMDB metadata

5. **Chunk**
   - Properties: chunk_id, text, chunk_index, text_length
   - Contains actual movie script text chunks

### Relationships:
1. **(Person)-[:ACTED_IN]->(Movie)**
   - Properties: character (text), ordering (int)
   - Actor/actress performed in a movie
   - Note: The character property contains IMDB character data (e.g., '["James Bond"]')

2. **(Person)-[:DIRECTED]->(Movie)**
   - Director directed a movie

3. **(Movie)-[:HAS_GENRE]->(Genre)**
   - Movie belongs to a genre

4. **(Chunk)-[:BELONGS_TO]->(Movie)**
   - Script chunk belongs to a movie

5. **(Character)-[:APPEARS_IN]->(Movie)**
   - Character appears in a movie

6. **(Chunk)-[:MENTIONS]->(Character)**
   - Script chunk mentions a character
   - This is the PRIMARY way to find dialogue/script content for characters

7. **(Character)-[:PORTRAYED_BY]->(Person)**
   - Properties: ordering (int)
   - Links script-extracted characters to the actors who played them
   - Note: This relationship may not exist for all characters due to name matching limitations

### Important Notes:
- All text properties are stored in lowercase for case-insensitive matching
- Person names and character names are lowercase
- Genre names are lowercase
- Use case-insensitive matching with toLower() function when searching
- The graph is chunk-centric: every movie has associated script chunks
- Character nodes come from script extraction and may have different names than IMDB character metadata
- PORTRAYED_BY relationships connect some (but not all) Character nodes to Person nodes
"""


class CypherQuery(BaseModel):
    """Structured output for Cypher query generation"""
    query: str
    explanation: str


class CypherQueryError(Exception):
    """Exception raised when Cypher query execution fails."""

    def __init__(self, query: str, error: Exception):
        self.query = query
        self.error = error
        self.error_message = str(error)
        super().__init__(f"Query failed: {self.error_message}")


class GraphQueryGenerator:
    """Generates and executes Cypher queries from natural language questions using LLM.

    Features:
    - LLM-based query generation from natural language
    - Self-correction when queries fail
    - Comprehensive error handling
    - Support for chunk retrieval
    """

    def __init__(self, uri: str, user: str, password: str, openai_api_key: Optional[str] = None):
        """Initialize the graph query generator.

        Args:
            uri: Neo4j connection URI (e.g., "bolt://localhost:7687")
            user: Neo4j username
            password: Neo4j password
            openai_api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        """
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.client = OpenAI(api_key=openai_api_key or os.getenv("OPENAI_API_KEY"))

    def close(self):
        """Close the Neo4j driver connection."""
        self.driver.close()

    def generate_cypher_query(
        self,
        question: str,
        limit: int = 10,
        previous_query: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> CypherQuery:
        """Generate Cypher query from natural language question using LLM.

        Args:
            question: Natural language question
            limit: Maximum number of chunks to return
            previous_query: If provided, attempt self-correction of this failed query
            error_message: Error message from the failed query

        Returns:
            CypherQuery with generated query and explanation
        """

        # Build the comprehensive prompt with all rules and examples
        prompt = f"""
        You are a Cypher query expert. Given the following graph schema and a user question,
        generate a Cypher query to answer the question.

        {GRAPH_SCHEMA}

        User Question: {question}

        SYNTAX RULES (MUST FOLLOW EXACTLY):
        1. NEVER EVER use EXISTS() function - it is deprecated and will cause a syntax error
        2. Instead of "EXISTS(variable.property)", ALWAYS use "variable.property IS NOT NULL"
        3. Use case-insensitive matching with toLower() for names and titles
        4. The ACTED_IN relationship has a "character" property containing the character name
        5. MENTIONS relationship goes directly from Chunk to Character (not Chunk->Movie->Character)

        EXAMPLES OF WRONG vs CORRECT SYNTAX:
        WRONG (will fail): WHERE EXISTS(ch.text)
        CORRECT: WHERE ch.text IS NOT NULL

        WRONG (will fail): WHERE EXISTS(m.title)
        CORRECT: WHERE m.title IS NOT NULL

        CRITICAL: AVOID THE DUPLICATE CHUNKS ANTI-PATTERN
        NEVER do this pattern:
        ```
        WITH m, collect(DISTINCT ch.text) as chunks
        MATCH (p:Person)-[a:ACTED_IN]->(m)
        RETURN p.name, chunks  // This gives same chunks to all actors!
        ```

        CRITICAL: AVOID COMPLEX CHARACTER NAME MATCHING
        DO NOT try to match ACTED_IN.character property with Character node names:
        ```
        MATCH (p:Person)-[a:ACTED_IN]->(m:Movie)
        WITH a.character as char_from_imdb
        MATCH (c:Character)-[:APPEARS_IN]->(m)
        WHERE toLower(c.name) = toLower(char_from_imdb)  // This often FAILS!
        ```

        Why this fails:
        - ACTED_IN.character contains IMDB data like '["James Bond"]' or '["007"]'
        - Character nodes are extracted from scripts with names like "bond", "james", "007"
        - These rarely match exactly, causing queries to return 0 results

        Instead, query Character nodes directly by name or use fuzzy matching (CONTAINS).

        Instead, use one of these patterns:

        PATTERN 1 - Return actors and chunks separately:
        ```
        MATCH (p:Person)-[a:ACTED_IN]->(m:Movie)
        WHERE toLower(m.title) = 'movie_name'
        RETURN p.name as actor, a.character as character_played
        ```

        GOOD PATTERN - Actor/Director queries:
        ```
        MATCH (p:Person)-[:ACTED_IN]->(m:Movie)
        WHERE toLower(p.name) = 'actor_name'
        WITH DISTINCT m.title as movie_title, m
        OPTIONAL MATCH (ch:Chunk)-[:BELONGS_TO]->(m)
        WITH movie_title, collect(ch.text)[0..{limit}] as chunks
        RETURN movie_title, chunks
        ```

        GOOD PATTERN - Specific movie questions:
        ```
        MATCH (m:Movie)
        WHERE toLower(m.title) CONTAINS 'movie_name'
        WITH m
        MATCH (ch:Chunk)-[:BELONGS_TO]->(m)
        RETURN m.title as movie_title, collect(ch.text)[0..{limit}] as chunks
        ```

        GOOD PATTERN - Character dialogue queries (RECOMMENDED):
        For questions like "What did X say to Y in movie Z?":
        ```
        MATCH (p:Person)-[a:ACTED_IN]->(m:Movie)
        WHERE toLower(p.name) CONTAINS 'actor_name' AND toLower(m.title) CONTAINS 'movie_name'
        WITH m, p, a.character as character_from_imdb
        MATCH (ch:Chunk)-[:BELONGS_TO]->(m)
        MATCH (ch)-[:MENTIONS]->(target:Character)
        WHERE toLower(target.name) CONTAINS 'target_character_name'
        RETURN m.title, p.name, character_from_imdb, collect(DISTINCT ch.text)[0..{limit}] as chunks
        ```

        Key points for character queries:
        - Use MENTIONS relationship to find chunks with specific characters
        - Use CONTAINS for fuzzy character name matching (e.g., "bond", "james bond", "007")
        - For multi-word character names (e.g., "Alec Trevelyan"), try matching on individual name components
          since Character nodes may only contain last names or first names
        - Don't try to match ACTED_IN.character with Character node names
        - Keep it simple: find movie + actor, then find chunks mentioning target character

        GOOD PATTERN - Finding chunks mentioning multiple characters:
        ```
        MATCH (m:Movie)
        WHERE toLower(m.title) CONTAINS 'movie_name'
        MATCH (ch:Chunk)-[:BELONGS_TO]->(m)
        MATCH (ch)-[:MENTIONS]->(char1:Character)
        WHERE toLower(char1.name) CONTAINS 'character1_name'
        OPTIONAL MATCH (ch)-[:MENTIONS]->(char2:Character)
        WHERE toLower(char2.name) CONTAINS 'character2_name'
        RETURN m.title, collect(DISTINCT ch.text)[0..{limit}] as chunks
        ```

        PROGRAMMATIC STRATEGIES FOR ROLE-BASED QUESTIONS (e.g., villain, hero, protagonist):
        1. Search script chunks for context words that indicate roles:
           - For villains: words like "evil", "betray", "enemy", "destroy", "kill", "revenge"
           - For heroes: words like "save", "rescue", "protect", "hero", "brave"
        2. Analyze character interactions in chunks
        3. Look for character names that appear frequently with conflict-related terms
        4. Use the ACTED_IN relationship's character property to find character names

        Generate a Cypher query that:
        1. Uses programmatic detection based on graph data only
        2. Does NOT hardcode any specific names or assumptions
        3. Properly traverses graph relationships
        4. AVOIDS the duplicate chunks anti-pattern
        5. Returns both metadata (movie titles, names, etc.) AND sample chunks
        6. Uses correct Neo4j syntax (no EXISTS()!)
        7. When returning chunks, ALWAYS name the field 'chunks' (not 'sample_dialogue', 'dialogue', or any other name)

        Return the query and a brief explanation of what it does.
        """

        # If we're doing self-correction, append the error context to the comprehensive prompt
        if previous_query and error_message:
            prompt += f"""

        IMPORTANT: The previous query attempt failed with an error. Please fix it.

        Failed Query:
        {previous_query}

        Error Message:
        {error_message}

        Generate a corrected version of the query that fixes the error while following all the rules above.
        """
            system_message = "You are a Cypher query expert for Neo4j. Fix the error while following all syntax rules and patterns."
        else:
            system_message = """
            You are a Cypher query expert for Neo4j. Return both metadata and chunks.
            """

        try:
            response = self.client.beta.chat.completions.parse(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                response_format=CypherQuery,
                temperature=0
            )

            return response.choices[0].message.parsed

        except Exception as e:
            print(f"Error generating query: {e}")
            # Fallback query
            return CypherQuery(
                query=f"MATCH (m:Movie) WITH m LIMIT 3 OPTIONAL MATCH (ch:Chunk)-[:BELONGS_TO]->(m) RETURN m.title as movie_title, collect(ch.text)[0..{limit}] as chunks",
                explanation="Fallback query returning sample movies and chunks"
            )

    def execute_query(self, cypher_query: str) -> List[Dict[str, Any]]:
        """Execute Cypher query and return results.

        Args:
            cypher_query: The Cypher query to execute

        Returns:
            List of result records as dictionaries

        Raises:
            CypherQueryError: If query execution fails
        """
        with self.driver.session() as session:
            try:
                result = session.run(cypher_query)
                return [dict(record) for record in result]
            except Exception as e:
                # Raise exception instead of returning empty list
                raise CypherQueryError(cypher_query, e)

    def query_with_retry(
        self,
        question: str,
        limit: int = 10,
        verbose: bool = True
    ) -> Tuple[CypherQuery, List[Dict[str, Any]]]:
        """Generate and execute query with automatic retry on failure.

        Args:
            question: Natural language question
            limit: Maximum number of chunks to return
            verbose: Whether to print status messages

        Returns:
            Tuple of (CypherQuery, results)
        """
        cypher_result = self.generate_cypher_query(question, limit=limit)

        if verbose:
            print(f"Generated Cypher Query:")
            print(f"   {cypher_result.query}")

        try:
            # Try executing the initial query
            results = self.execute_query(cypher_result.query)

            if verbose:
                print(f"   → Retrieved {len(results)} results from graph")

            return cypher_result, results

        except CypherQueryError as e:
            # Query failed - try self-correction
            if verbose:
                print(f"Initial query failed: {e.error_message[:100]}...")
                print(f"Attempting self-correction...")

            # Ask LLM to fix the query based on the error
            corrected_result = self.generate_cypher_query(
                question,
                limit=limit,
                previous_query=cypher_result.query,
                error_message=e.error_message
            )

            try:
                # Try executing the corrected query
                results = self.execute_query(corrected_result.query)

                if verbose:
                    print(f"Corrected query succeeded!")
                    print(f"   {corrected_result.query}...")
                    print(f"   → Retrieved {len(results)} results from graph")

                return corrected_result, results

            except CypherQueryError as e2:
                # Even the corrected query failed - give up and return empty results
                if verbose:
                    print(f"Corrected query also failed: {e2.error_message[:100]}...")
                    print(f"   Returning empty results")

                return corrected_result, []

    def query_with_chunks(
        self,
        question: str,
        limit: int = 10,
        include_chunks: bool = True,
        verbose: bool = True
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Generate and execute query, optionally retrieving associated chunks.

        This is a convenience method that combines query generation, execution,
        and optional chunk retrieval.

        Args:
            question: Natural language question
            limit: Maximum number of chunks to return
            include_chunks: Whether to fetch chunks if not in query results
            verbose: Whether to print status messages

        Returns:
            Tuple of (query_string, results)
        """
        cypher_result, results = self.query_with_retry(question, limit=limit, verbose=verbose)

        if verbose:
            print(f"\nExplanation: {cypher_result.explanation}")

        # If chunks should be included and weren't in original query, fetch them
        if include_chunks and results and 'chunk' not in cypher_result.query.lower():
            # Extract movie IDs from results
            movie_ids = set()
            for record in results:
                for key, value in record.items():
                    if isinstance(value, dict) and 'imdb_id' in value:
                        movie_ids.add(value['imdb_id'])

            if movie_ids:
                # Fetch relevant chunks for these movies
                chunk_query = f"""
                MATCH (ch:Chunk)-[:BELONGS_TO]->(m:Movie)
                WHERE m.imdb_id IN {list(movie_ids)}
                RETURN ch.text as chunk_text, m.title as movie_title
                ORDER BY m.title, ch.chunk_index
                LIMIT {limit}
                """
                try:
                    chunks = self.execute_query(chunk_query)
                    if chunks:
                        results.append({'related_chunks': chunks})
                except CypherQueryError:
                    pass  # Ignore chunk retrieval errors

        return cypher_result.query, results
