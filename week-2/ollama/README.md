# Week 2 — Running an LLM on a Virtual Machine

## Objective

Install and run a local Large Language Model (LLM) on the Ubuntu Virtual Machine and interact with it through prompts.

## Environment

- VM: `ai-devops-lab`
- OS: Ubuntu 26.04 LTS
- Architecture: ARM64 (`aarch64`)
- RAM: 6 GB
- Execution: CPU-only
- Runtime: Ollama
- Model: Qwen2.5-Coder 3B

## Ollama

Ollama is used to run LLMs locally and provides a local interface for interacting with installed models.

Check the installed version:

```bash
ollama --version
```

## Model

Qwen2.5-Coder 3B is a code-focused language model used for programming-related tasks such as code generation, explanation, and problem solving.

Install the model:

```bash
ollama pull qwen2.5-coder:3b
```

Verify installed models:

```bash
ollama list
```

## Running the Model

Start the model locally:

```bash
ollama run qwen2.5-coder:3b
```

A Python programming prompt was provided to the model to verify its ability to generate and explain code.

## Verification

The model successfully executed locally on the Virtual Machine.

The model runs using CPU because the VM does not have access to a dedicated GPU.

## Week 2 VM Outcome

Successfully demonstrated:

1. Local LLM installation
2. Model management using Ollama
3. Local model execution
4. Prompt-based interaction
5. Code generation using a local LLM

These concepts form the foundation for later AI application and RAG workflows.
