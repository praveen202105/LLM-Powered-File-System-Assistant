"""
Example usage of the File System Assistant with LLM integration.
Demonstrates how to use OpenAI, Anthropic, and Groq providers.
"""

from backend.llm_file_assistant import FileAssistant, OpenAIProvider, AnthropicProvider, GroqProvider


def example_with_anthropic():
    """Example using Anthropic Claude as the LLM provider."""
    try:
        provider = AnthropicProvider()
        assistant = FileAssistant(provider)

        queries = [
            "List all resume files in sample_data/resumes/",
            "Find resumes mentioning Python",
            "Which resumes mention AWS or cloud platforms?",
            "Create a summary file listing all developers and their primary skills",
            "Search for resumes with both Python and Go experience"
        ]

        print("=" * 60)
        print("File System Assistant - Anthropic Example")
        print("=" * 60)

        for i, query in enumerate(queries, 1):
            print(f"\nQuery {i}: {query}")
            print("-" * 60)
            response = assistant.run(query)
            print(f"Response:\n{response}")
            print()

    except Exception as e:
        print(f"Anthropic example failed: {str(e)}")
        print("Ensure ANTHROPIC_API_KEY is set in environment variables")


def example_with_openai():
    """Example using OpenAI GPT as the LLM provider."""
    try:
        provider = OpenAIProvider(model="gpt-4")
        assistant = FileAssistant(provider)

        queries = [
            "List all resume files in sample_data/resumes/",
            "Find all mentions of Docker in the resumes",
            "Which developers have Kubernetes experience?",
        ]

        print("=" * 60)
        print("File System Assistant - OpenAI Example")
        print("=" * 60)

        for i, query in enumerate(queries, 1):
            print(f"\nQuery {i}: {query}")
            print("-" * 60)
            response = assistant.run(query)
            print(f"Response:\n{response}")
            print()

    except Exception as e:
        print(f"OpenAI example failed: {str(e)}")
        print("Ensure OPENAI_API_KEY is set in environment variables")


def example_with_groq():
    """Example using Groq as the LLM provider."""
    try:
        provider = GroqProvider(model="llama-3.1-8b-instant")
        assistant = FileAssistant(provider)

        queries = [
            "List all resume files in sample_data/resumes/",
            "Find resumes mentioning Python",
            "Which developers have Kubernetes experience?",
        ]

        print("=" * 60)
        print("File System Assistant - Groq Example")
        print("=" * 60)

        for i, query in enumerate(queries, 1):
            print(f"\nQuery {i}: {query}")
            print("-" * 60)
            response = assistant.run(query)
            print(f"Response:\n{response}")
            print()

    except Exception as e:
        print(f"Groq example failed: {str(e)}")
        print("Ensure GROQ_API_KEY is set in environment variables")


def example_file_operations_only():
    """
    Example using only fs_tools without LLM.
    Useful for testing and understanding the tool APIs.
    """
    from backend.fs_tools import read_file, list_files, search_in_file

    print("=" * 60)
    print("File System Tools - Direct Usage Example")
    print("=" * 60)

    print("\n1. Listing resume files:")
    print("-" * 60)
    files = list_files("sample_data/resumes/", ".txt")
    for file in files:
        print(f"  {file['filename']} ({file['size_bytes']} bytes)")

    print("\n2. Reading a resume:")
    print("-" * 60)
    result = read_file("sample_data/resumes/resume_john_doe.txt")
    if result["success"]:
        content_preview = result["content"][:200] + "..."
        print(f"Content preview:\n{content_preview}")
        print(f"\nMetadata: {result['metadata']}")

    print("\n3. Searching for a keyword:")
    print("-" * 60)
    search_result = search_in_file("sample_data/resumes/resume_john_doe.txt", "Python")
    print(f"Found {search_result['match_count']} matches for 'Python':")
    for match in search_result["matches"][:2]:
        print(f"  Line {match['line_number']}: {match['match_text']}")

    print("\n4. Writing a summary file:")
    print("-" * 60)
    summary = """Resume Analysis Summary
=====================

Total Resumes: 6

Languages and Technologies:
- Python: 3 resumes
- Go: 1 resume
- JavaScript: 2 resumes
- Java: 1 resume
- Swift: 1 resume

Cloud Platforms:
- AWS: 4 resumes
- Google Cloud: 2 resumes
- Kubernetes: 2 resumes

Top Skills:
- Python (Data Science, Backend)
- AWS (Infrastructure)
- Kubernetes (DevOps)
- React (Frontend)
"""

    write_result = write_file("sample_data/resumes/SUMMARY.txt", summary)
    if write_result["success"]:
        print(f"Summary written to: {write_result['filepath']}")


if __name__ == "__main__":
    print("\nChoose an example to run:")
    print("1. File Operations Only (no LLM)")
    print("2. Anthropic Provider Example")
    print("3. OpenAI Provider Example")
    print("4. Groq Provider Example")

    choice = input("\nEnter choice (1-4): ").strip()

    if choice == "1":
        example_file_operations_only()
    elif choice == "2":
        example_with_anthropic()
    elif choice == "3":
        example_with_openai()
    elif choice == "4":
        example_with_groq()
    else:
        print("Invalid choice. Running file operations example...")
        example_file_operations_only()
