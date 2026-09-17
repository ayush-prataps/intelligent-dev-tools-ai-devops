# Week 4 – Multi-Model Evaluation and RAG Analysis

## Project

**University Knowledge Assistant**

This work continues the same LLM application developed during Week 3.

The application uses:

- FastAPI for the application and service APIs
- Ollama for local LLM inference
- Code Llama, Phi-3 Mini, and Qwen 2.5 3B as evaluated generation models
- `nomic-embed-text` for embeddings
- Local JSON knowledge base containing university policy documents
- Cosine similarity for vector retrieval
- Docker Compose for the application, retrieval, and LLM services

The overall architecture is:

```text
User
  ↓
Application Service
  ↓
Retrieval Service
  ↓
Embedding + Cosine Similarity
  ↓
Relevant Context
  ↓
LLM Service
  ↓
Ollama
  ↓
Generation Model
  ↓
Final Response
```

---

## Exercise 1 – Evaluate Multiple LLM / Code Models

### Objective

Evaluate at least three different LLM/code models using the same application and evaluation conditions.

### Models Evaluated

The following three local models were evaluated:

- `codellama:7b-instruct`
- `phi3:mini`
- `qwen2.5:3b`

All models were evaluated using the same:

- University Knowledge Assistant application
- Knowledge base
- Embedding model
- Retrieval implementation
- Retrieval `top_k`
- Prompt structure
- Evaluation questions
- RAG workflow

The generation model was the primary variable.

### Evaluation Procedure

The evaluation was divided into two phases.

#### Phase 1 – Retrieval

The 20 evaluation questions were sent through the retrieval service.

For every question, the system:

1. Generated an embedding using `nomic-embed-text`.
2. Compared the question embedding against the stored knowledge-base vectors.
3. Selected the top 3 chunks using cosine similarity.
4. Stored the retrieved results in `week-4/results/retrieval_results.json`.

The retrieval results were frozen before evaluating the generation models.

#### Phase 2 – Model Evaluation

Each generation model was evaluated using the same 20 questions and the corresponding frozen retrieval results.

For each question, the system recorded:

- Question
- Retrieved context
- Generated answer
- Prompt token count
- Output token count
- Total latency
- Runtime errors

All three models completed the 20-question evaluation without runtime errors, storing results in:
- `week-4/results/codellama_7b-instruct_results.json`
- `week-4/results/phi3_mini_results.json`
- `week-4/results/qwen2.5_3b_results.json`

---

## Exercise 2 – Create Evaluation Dataset

### Objective

Create a representative evaluation dataset containing approximately 20–30 questions related to the actual application use case.

A standardized dataset of 20 questions was created for the University Knowledge Assistant.

The same dataset was used for all three models.

### Dataset Categories

| Category | Number of Questions |
|---|---|
| Direct factual | 4 |
| Multi-condition reasoning | 4 |
| Policy comparison | 3 |
| Procedure | 3 |
| Edge cases | 3 |
| Insufficient context | 1 |
| Multi-document | 2 |
| **Total** | **20** |

### Evaluation Questions

The questions cover university attendance, leave, grading, academic probation, examinations, campus facilities, and related policies.

The final dataset uses IDs Q01 through Q20 and is stored in:

`week-4/data/evaluation_questions.json`

The same questions were used for every evaluated model to maintain a controlled comparison.

---

## Exercise 3 – Quantitative Evaluation

### Objective

Measure both quality and performance characteristics of the evaluated models.

The following metrics were used:

#### Quality Metrics
- Correctness / Accuracy
- Relevance
- Retrieval Quality
- Hallucination Rate
- Test-Pass Rate

#### Performance Metrics
- Response Latency
- Token Usage
- CPU Usage
- Memory Usage
- GPU Usage

### 3.1 Correctness / Accuracy

Correctness was manually evaluated against the ground-truth university policy information. For each model response, a score of 0, 1, or 2 was assigned according to the rubric, and these labels were then programmatically aggregated using `week-4/evaluation/score_results.py`.

A 0–2 scoring rubric was used:

| Score | Meaning |
|---|---|
| 2 | Correct |
| 1 | Partially correct |
| 0 | Incorrect |

The final score was calculated as:

$$\text{Correctness (\%)} = \left(\frac{\text{Total correctness points}}{\text{Maximum possible points}}\right) \times 100$$

There were 20 questions and a maximum of 2 points per question, giving a maximum score of 40.

Results:

| Model | Score | Correctness |
|---|---|---|
| Code Llama 7B | 34 / 40 | 85% |
| Phi-3 Mini | 40 / 40 | 100% |
| Qwen 2.5 3B | 38 / 40 | 95% |

### 3.2 Relevance

Relevance was manually evaluated against the specific inquiry. Scores of 0, 1, or 2 were assigned to each response according to the rubric and aggregated by `week-4/evaluation/score_results.py`:

| Score | Meaning |
|---|---|
| 2 | Directly relevant |
| 1 | Partially relevant / unnecessary or missing information |
| 0 | Not relevant |

Results:

| Model | Score | Relevance |
|---|---|---|
| Code Llama 7B | 30 / 40 | 75% |
| Phi-3 Mini | 37 / 40 | 92.5% |
| Qwen 2.5 3B | 40 / 40 | 100% |

### 3.3 Retrieval Quality

Retrieval quality was evaluated independently from the generation model.

The retrieved chunks were compared against the ground-truth expected source document and section for each question in the dataset.

The retrieval results were frozen and reused across all three models. Therefore, all models received the exact same retrieved context.

Retrieval Quality was calculated as:

$$\text{Retrieval Quality} = \frac{\text{Correctly retrieved relevant questions}}{\text{Answerable questions}} \times 100 = \frac{14}{19} \times 100 = 73.68\%$$

> *Note:* Question Q18 was excluded from the denominator because it is intentionally an insufficient-context question designed to test how models handle missing knowledge-base documentation.

The measured retrieval quality was:

**73.68%**

for all three models.

This demonstrates that retrieval quality is an independent component of the RAG pipeline and should not be confused with LLM response quality.

### 3.4 Hallucination Rate

Hallucination was evaluated as a binary metric (0 = no unsupported claims, 1 = at least one unsupported factual claim introduced). Labels were manually assigned by comparing each response strictly against the provided context chunks and aggregated via `week-4/evaluation/score_results.py`.

| Value | Meaning |
|---|---|
| 0 | No hallucination |
| 1 | Hallucination |

The hallucination rate was calculated as:

$$\text{Hallucination Rate} = \left(\frac{\text{Number of hallucinated responses}}{\text{Total responses}}\right) \times 100$$

Results:

| Model | Hallucinated Responses | Hallucination Rate |
|---|---|---|
| Code Llama 7B | 8 / 20 | 40% |
| Phi-3 Mini | 1 / 20 | 5% |
| Qwen 2.5 3B | 1 / 20 | 5% |

### 3.5 Test-Pass Rate

Test-pass rate was not applicable to this application.

The University Knowledge Assistant generates natural-language answers to university policy questions. It does not generate executable programs or code requiring automated test cases.

Therefore:

**Test-Pass Rate = N/A**

### 3.6 Response Latency

Response latency was measured for the model generation request.

| Model | Average Latency | Median Latency |
|---|---|---|
| Code Llama 7B | 19,322.82 ms | 17,366.62 ms |
| Phi-3 Mini | 11,440.03 ms | 8,097.61 ms |
| Qwen 2.5 3B | 6,241.39 ms | 5,828.70 ms |

Average latency in seconds:

| Model | Average Latency |
|---|---|
| Code Llama 7B | 19.32 s |
| Phi-3 Mini | 11.44 s |
| Qwen 2.5 3B | 6.24 s |

Phi-3 Mini had one significant latency outlier for Q20, where the response took approximately 72 seconds and produced substantially more output tokens. The measurement was retained because it was an actual evaluation result.

### 3.7 Token Usage

Total token usage was calculated as:

$$\text{Total Tokens} = \text{Prompt Tokens} + \text{Output Tokens}$$

Results:

| Model | Average Total Tokens |
|---|---|
| Code Llama 7B | 682.65 |
| Phi-3 Mini | 676.30 |
| Qwen 2.5 3B | 523.35 |

Qwen 2.5 3B used the fewest tokens on average.

### 3.8 CPU Usage

Resource monitoring was performed during an actual RAG request using `pidstat`.

The Ubuntu VM has four CPU cores.

CPU usage reported by `pidstat` is relative to one CPU, meaning approximately 400% represents utilization of all four cores.

| Model | Average CPU | Peak CPU |
|---|---|---|
| Code Llama 7B | 108.90% | 400% |
| Phi-3 Mini | 182.58% | 400% |
| Qwen 2.5 3B | 165.33% | 399% |

### 3.9 Memory Usage

Memory was measured using the resident memory (RSS) of the active `llama-server` model process during inference.

| Model | Average RSS | Peak RSS |
|---|---|---|
| Code Llama 7B | 5.26 GiB | 5.83 GiB |
| Phi-3 Mini | 4.93 GiB | 5.83 GiB |
| Qwen 2.5 3B | 4.78 GiB | 5.81 GiB |

These measurements represent the memory used by the running model server process rather than the model file size.

The measurements were performed with one generation model loaded at a time to avoid cross-model memory contamination.

### 3.10 GPU Usage

The models were executed using CPU-only inference on the Ubuntu VM.

| Model | GPU Usage |
|---|---|
| Code Llama 7B | 0 |
| Phi-3 Mini | 0 |
| Qwen 2.5 3B | 0 |

No GPU acceleration was used during the evaluation.

---

## Exercise 4 – Quantitative Analysis and Model Comparison

### 4.1 Overall Results

| Metric | Code Llama 7B | Phi-3 Mini | Qwen 2.5 3B |
|---|---|---|---|
| Correctness | 85% | 100% | 95% |
| Relevance | 75% | 92.5% | 100% |
| Retrieval Quality | 73.68% | 73.68% | 73.68% |
| Hallucination Rate | 40% | 5% | 5% |
| Average Latency | 19.32 s | 11.44 s | 6.24 s |
| Median Latency | 17.37 s | 8.10 s | 5.83 s |
| Avg. Total Tokens | 682.65 | 676.30 | 523.35 |
| Average CPU | 108.90% | 182.58% | 165.33% |
| Peak RSS | 5.83 GiB | 5.83 GiB | 5.81 GiB |
| GPU | 0 | 0 | 0 |
| Test-Pass Rate | N/A | N/A | N/A |

### 4.2 Quality Analysis

Correctness differed between the three models despite the models receiving the same retrieved context.

Measured correctness:

- **Code Llama**: 85%
- **Phi-3 Mini**: 100%
- **Qwen 2.5 3B**: 95%

Relevance followed a similar pattern:

- **Code Llama**: 75%
- **Phi-3 Mini**: 92.5%
- **Qwen 2.5 3B**: 100%

The largest difference was observed in hallucination rate.

Code Llama produced hallucinations in 8 of the 20 evaluated responses, giving a measured hallucination rate of 40%.

Phi-3 Mini and Qwen 2.5 3B each produced one hallucinated response, giving a measured rate of 5%.

### 4.3 Retrieval vs. Generation

Retrieval quality was 73.68% for all models because the retrieval results were frozen before generation evaluation.

This provides an important separation:

```text
Retrieval Quality
       ↓
Retrieved Context
       ↓
Generation Model
       ↓
Final Response
```

An incorrect response can therefore result from different stages of the pipeline.

If relevant information is not retrieved, the model does not receive that information in its context.

If the relevant information is retrieved but the final answer is incorrect or unsupported, the problem may instead involve how the generation model interpreted or used the context.

### 4.4 Latency Analysis

Average latency:

- **Code Llama**: 19.32 seconds
- **Phi-3 Mini**: 11.44 seconds
- **Qwen 2.5 3B**: 6.24 seconds

Median latency followed the same general ordering:

- **Code Llama**: 17.37 seconds
- **Phi-3 Mini**: 8.10 seconds
- **Qwen 2.5 3B**: 5.83 seconds

This indicates that the latency difference was not caused only by a single extreme measurement.

The evaluation measured substantial latency differences under this workload and environment.

### 4.5 Token Usage Analysis

Average total token usage:

- **Code Llama**: 682.65
- **Phi-3 Mini**: 676.30
- **Qwen 2.5 3B**: 523.35

Qwen generated shorter responses on average and therefore consumed fewer total tokens.

Since the prompt contained the same retrieved context structure for the compared questions, differences in total token usage were primarily associated with the generated output.

### 4.6 Resource Analysis

All three models used substantial CPU resources during inference because the evaluation was performed on a CPU-only four-core VM.

Peak CPU usage reached approximately 400% for all three models.

Peak RSS was also similar:

- **Code Llama**: 5.83 GiB
- **Phi-3 Mini**: 5.83 GiB
- **Qwen 2.5 3B**: 5.81 GiB

An important observation is that model file size does not directly translate into peak runtime RSS.

The RSS measurement includes memory used by the running `llama-server`, including runtime allocations and buffers.

### 4.7 Accuracy vs. Efficiency

The results demonstrate that model quality and execution efficiency are separate dimensions.

Code Llama produced:
- 85% correctness
- 75% relevance
- 40% hallucination rate
- 19.32 s average latency

Phi-3 Mini produced:
- 100% correctness
- 92.5% relevance
- 5% hallucination rate
- 11.44 s average latency

Qwen 2.5 3B produced:
- 95% correctness
- 100% relevance
- 5% hallucination rate
- 6.24 s average latency

Therefore, model size alone does not determine the measured quality or efficiency of the RAG application.

### 4.8 Quality–Latency–Resource Trade-off

The experiment demonstrates the importance of evaluating multiple dimensions simultaneously.

#### Quality
The measured correctness and hallucination results differed substantially between the models.

#### Latency
The models also showed substantial differences in response latency.

#### Resources
Peak RSS was approximately 5.8 GiB for all three models, while CPU utilization was high during inference.

This demonstrates that model evaluation should consider:

```text
Quality
   +
Latency
   +
Token Usage
   +
Resource Consumption
```

rather than relying on a single metric.

### 4.9 Key Findings

- The same RAG pipeline produced different response quality depending on the generation model.
- Retrieval quality remained constant at 73.68% because retrieval results were frozen.
- Code Llama had a measured correctness of 85% and hallucination rate of 40%.
- Phi-3 Mini had a measured correctness of 100% and hallucination rate of 5%.
- Qwen 2.5 3B had a measured correctness of 95% and hallucination rate of 5%.
- Qwen 2.5 3B had the lowest measured average latency at 6.24 seconds.
- Qwen 2.5 3B also had the lowest average total token usage at 523.35 tokens.
- Peak RSS was approximately 5.8 GiB for all three models.
- All three models used CPU-only inference and reached approximately 400% peak CPU utilization on the four-core VM.
- Test-pass rate was not applicable because the application does not generate executable code.

---

## Exercise 5 – Evidence-Based RAG Pipeline Analysis

### Objective

Analyze the existing RAG pipeline beyond simply verifying that retrieval works, using exact recorded evidence from the evaluation dataset:

```text
QUESTION
   ↓
RETRIEVED CONTEXT
   ↓
LLM RESPONSE
```

The goal is to determine:

- Whether the retrieved information was relevant and complete.
- How the models utilized the provided context.
- Whether hallucinations occurred despite relevant context.
- How retrieval quality directly impacts final response quality.

### 5.1 RAG Pipeline Architecture

The University Knowledge Assistant uses the following retrieval and generation flow:

```text
Student Question
       ↓
Question Embedding (nomic-embed-text)
       ↓
Cosine Similarity Search
       ↓
Top 3 Knowledge Chunks
       ↓
Context Construction
       ↓
Augmented Prompt
       ↓
LLM Generation
       ↓
Grounded Answer
```

For each evaluated question, the frozen retrieval stage recorded the top-3 retrieved chunks (document title, section, cosine similarity score, and text). All three generation models received this identical context.

---

### 5.2 Case 1 (Q01) – Direct Factual Retrieval and Uniform Success

#### Question
> **Q01**: *"What is the minimum attendance requirement for a student to be eligible for end-semester examinations?"*  
> **Expected Answer**: Students must maintain at least 75% attendance in each enrolled theory and laboratory course.

#### Retrieved Context Chunks (Frozen Record)
1. **University Attendance Policy** > *Minimum Attendance Requirement* (Similarity: **0.9108**)  
   `"All registered undergraduate and postgraduate students must maintain a minimum attendance of 75% in each enrolled theory and laboratory course during a semester to be eligible for end-semester examinations..."`
2. **University Attendance Policy** > *Condonation of Attendance Shortage* (Similarity: **0.7739**)  
   `"Students with attendance between 65% and 74.9% may apply to the Dean of Academic Affairs for attendance condonation on genuine medical or compassionate grounds..."`
3. **University Attendance Policy** > *Debarment Due to Attendance Shortage* (Similarity: **0.7731**)  
   `"Students with aggregate course attendance below 65% under any circumstances are considered critically deficient..."`

#### Actual Model Responses

- **Code Llama 7B**:
  > *"The minimum attendance requirement for a student to be eligible for end-semester examinations is 75%. This is stated in the University Attendance Policy under the 'Minimum Attendance Requirement' section."*

- **Phi-3 Mini**:
  > *"According to the University Attendance Policy, to be eligible for end-semester examinations, all registered undergraduate and postgraduate students must maintain a minimum attendance of 75% in each enrolled theory and laboratory course during a semester. This attendance requirement is calculated from the official semester commencement date until the last instructional day announced in the academic calendar."*

- **Qwen 2.5 3B**:
  > *"According to the University Attendance Policy, the minimum attendance requirement for a student to be eligible for end-semester examinations is 75% in each enrolled theory and laboratory course during a semester."*

#### Analysis & Finding
- **Retrieval Quality**: Fully relevant (top chunk score 0.9108 directly answered the query).
- **Context Quality**: Directly contains the exact rule.
- **Model Behavior**: All three models extracted the 75% threshold without hallucination. Straightforward factual questions with high cosine similarity exhibit near 100% pipeline reliability across models.

---

### 5.3 Case 2 (Q05) – Multi-Condition Reasoning and Context Interpretation

#### Question
> **Q05**: *"A student has 70% attendance in a course due to hospitalization. Can they appear for the end-semester examination?"*  
> **Expected Answer**: They cannot automatically appear; however, because 70% falls within 65%–74.9%, they can apply for attendance condonation on medical grounds with a certificate within 7 working days, subject to Academic Review Board discretion.

#### Retrieved Context Chunks (Frozen Record)
1. **University Attendance Policy** > *Condonation of Attendance Shortage* (Similarity: **0.8650**)  
   `"Students with attendance between 65% and 74.9% may apply to the Dean of Academic Affairs for attendance condonation on genuine medical or compassionate grounds. The application must include an official medical certificate issued by a registered medical practitioner within seven working days of returning to campus, along with a nominal condonation fee. Condonation is granted at the sole discretion of the Academic Review Board."`
2. **University Attendance Policy** > *Minimum Attendance Requirement* (Similarity: **0.8166**)  
   `"All registered undergraduate and postgraduate students must maintain a minimum attendance of 75% in each enrolled theory and laboratory course during a semester to be eligible for end-semester examinations..."`
3. **University Attendance Policy** > *Debarment Due to Attendance Shortage* (Similarity: **0.7765**)  
   `"Students with aggregate course attendance below 65% under any circumstances are considered critically deficient and shall be formally debarred from appearing in the end-semester examination..."`

#### Actual Model Responses

- **Code Llama 7B**:
  > *"Based on the provided university policies, it is not explicitly stated whether a student with 70% attendance can appear for the end-semester examination... However, the policy does state that students with attendance between 65% and 74.9% may apply to the Dean of Academic Affairs for attendance condonation on genuine medical or compassionate grounds... Overall, the policies indicate that a student with 70% attendance can apply for attendance condonation on genuine medical or compassionate grounds, but the exact attendance percentage required for condonation is not specified."*

- **Phi-3 Mini**:
  > *"According to the University Attendance Policy, a student with attendance between 65% and 74.9% may apply for attendance condonation on genuine medical or compassionate grounds. However, to be considered for condonation, the student must submit an official medical certificate from a registered medical practitioner within seven working days of returning to campus, along with a nominal condonation fee. Once these requirements are met, condonation is granted at the sole discretion of the Academic Review Board. Therefore, without information on whether the student has met these conditions and been granted condonation by the Academic Review Board, we cannot say that the student will automatically appear for the examination."*

- **Qwen 2.5 3B**:
  > *"Based on the University Attendance Policy, a student with an attendance percentage of 70% falls within the range of 65% to 74.9%, which allows for an application for attendance condonation due to genuine medical grounds. The policy stipulates that an official medical certificate must be submitted along with an application for condonation to the Dean of Academic Affairs, along with a nominal fee. Since the policy states that condonation is granted at the sole discretion of the Academic Review Board, the student cannot automatically appear for the examination. The student must submit a valid application with the required documentation and await a decision from the Academic Review Board."*

#### Analysis & Finding
- **Retrieval Quality**: High (supplied minimum attendance, condonation 65%–74.9%, and debarment chunks).
- **Context Quality**: Contained the conditional clauses, documentation requirements, and discretionary authority.
- **Model Behavior**:
  - **Phi-3 Mini** and **Qwen 2.5 3B** reasoned correctly that 70% falls in the condonation band, outlined the required steps, and concluded that appearance is conditional rather than automatic.
  - **Code Llama 7B** experienced a context-interpretation breakdown: it quoted the 65%–74.9% range but concluded in its final sentence that *"the exact attendance percentage required for condonation is not specified"*, directly contradicting the context chunk. This highlights that **Retrieval Success $\neq$ Response Success**.

---

### 5.4 Case 3 (Q08) – Policy Comparison and Context Distraction

#### Question
> **Q08**: *"Can a student register for an advanced course if they have not passed its prerequisite but have a recommendation from the course instructor?"*  
> **Expected Answer**: No. A conditional prerequisite waiver requires both a written recommendation from the course instructor and approval by the Departmental Academic Committee prior to course registration.

#### Retrieved Context Chunks (Frozen Record)
1. **University Academic Policies and Degree Requirements** > *Course Prerequisite Policy* (Similarity: **0.8350**)  
   `"Students cannot register for an advanced course without successfully clearing the listed prerequisite subjects with a passing grade ('D' or higher). Any conditional prerequisite waiver requires written recommendation from the course instructor and approval by the Departmental Academic Committee prior to course registration."`
2. **University Academic Policies and Degree Requirements** > *Degree Credit Structure and Course Registration* (Similarity: **0.6600**)  
   `"Undergraduate engineering degree programs require the successful completion of a minimum of 160 academic credits..."`
3. **University Attendance Policy** > *Debarment Due to Attendance Shortage* (Similarity: **0.6358**)  
   `"Students with aggregate course attendance below 65% under any circumstances are considered critically deficient..."`

#### Actual Model Responses

- **Code Llama 7B**:
  > *"Based on the information provided, it is possible for a student to register for an advanced course if they have not passed its prerequisite but have a recommendation from the course instructor. However, there are some conditions to consider. Firstly, the recommendation from the course instructor must be in writing, and the student must provide this recommendation to the Departmental Academic Committee prior to course registration. The Departmental Academic Committee may review the recommendation and decide whether to approve the student's registration in the advanced course. Secondly, the student must still meet the minimum passing grade for the prerequisite course... Lastly, the student must ensure that they have completed the minimum number of credits... It is important to note that the University Attendance Policy also applies to advanced courses, and students with aggregate course attendance below 65% may be debarred..."*

- **Phi-3 Mini**:
  > *"According to the University Academic Policies and Degree Requirements, specifically the Course Prerequisite Policy, students are required to have passed the listed prerequisite subjects for an advanced course with a passing grade before they can register for it. Even if a student has a conditional prerequisite waiver with a written recommendation from the course instructor, approval by the Departmental Academic Committee is still necessary. Therefore, without this committee's approval, a student cannot register for an advanced course based solely on the instructor's recommendation."*

- **Qwen 2.5 3B**:
  > *"No, a student cannot register for an advanced course if they have not passed its prerequisite subjects. According to the University Academic Policies and Degree Requirements, students cannot register for an advanced course without successfully clearing the listed prerequisite subjects with a passing grade. Any conditional prerequisite waiver requires written recommendation from the course instructor and approval by the Departmental Academic Committee prior to course registration."*

#### Analysis & Finding
- **Retrieval Quality**: Partial / Distracted (Chunk 1 was directly relevant, but Chunks 2 and 3 contained irrelevant degree credits and attendance debarment).
- **Model Behavior**:
  - **Phi-3 Mini** and **Qwen 2.5 3B** ignored the distractor chunks and focused strictly on the prerequisite waiver clause.
  - **Code Llama 7B** was distracted by the irrelevant chunks, incorrectly claiming the student must complete all 160 credits and maintain 65% attendance to register for the prerequisite waiver. This shows how noisy top-k retrieval induces hallucinations in less disciplined models.

---

### 5.5 Case 4 (Q18) – Insufficient Context and Negative Constraint Handling

#### Question
> **Q18**: *"What is the university's policy for hostel room allocation?"*  
> **Expected Answer**: The provided knowledge base does not contain information about hostel room allocation.

#### Retrieved Context Chunks (Frozen Record)
1. **University Attendance Policy** > *Minimum Attendance Requirement* (Similarity: **0.6307**)  
   `"All registered undergraduate and postgraduate students must maintain a minimum attendance of 75% in each enrolled theory and laboratory course..."`
2. **University Attendance Policy** > *Condonation of Attendance Shortage* (Similarity: **0.6261**)  
   `"Students with attendance between 65% and 74.9% may apply to the Dean of Academic Affairs for attendance condonation..."`
3. **University Examination Rules and Regulations** > *Examination Hall Entry and Admit Card* (Similarity: **0.6238**)  
   `"Students must arrive at the examination hall at least 15 minutes before the scheduled commencement of the examination..."`

#### Expected vs. Observed Response Behavior
- **Expected Response Behavior**: Acknowledge insufficient information rather than inventing an unverified policy.

#### Actual Model Responses

- **Code Llama 7B**:
  > *"The university's policy for hostel room allocation is not explicitly stated in the provided context. However, based on the information provided, it seems that the university does not have a specific policy for hostel room allocation. The context provides information on the university's attendance policy, attendance condonation policy, and examination rules and regulations. However, it does not mention anything about hostel room allocation. Therefore, it seems that the university does not have a specific policy for hostel room allocation and students are allocated hostel rooms based on the university's discretion."*

- **Phi-3 Mini**:
  > *"I'm sorry, but the information provided does not contain specific details about the university's policy for hostel room allocation. The context given only discusses attendance requirements, the conditions for condonation of attendance shortages, and the rules for entering the examination hall. For information about hostel room allocation, please refer to the relevant university housing or accommodation policies."*

- **Qwen 2.5 3B**:
  > *"Based on the provided university policies, the question about hostel room allocation does not fall within the scope of the given context. The policies discussed cover attendance requirements and examination rules, but do not mention any information regarding hostel room allocation. Therefore, I cannot provide specific information about the university's policy on hostel room allocation using the given information."*

#### Analysis & Finding
- **Retrieval Quality**: Insufficient by design (knowledge base intentionally lacks a housing document; top-3 chunks are mathematical nearest neighbors with low similarity ~0.62).
- **Model Behavior**:
  - **Phi-3 Mini** and **Qwen 2.5 3B** successfully adhered to the negative constraint in the system prompt, stating that the context does not contain the answer.
  - **Code Llama 7B** recognized the absence of the policy, but then hallucinated an ungrounded procedural rule: *"and students are allocated hostel rooms based on the university's discretion"*.

---

### 5.6 Case 5 (Q20) – Multi-Document Synthesis: Condonation vs. Medical Leave

#### Question
> **Q20**: *"Can medical leave be used to condone attendance shortages?"*  
> **Expected Answer**: No. Medical leave (up to 15 days) recognizes authorized absence due to hospitalization, but attendance shortage condonation (for attendance between 65% and 74.9%) requires a separate application to the Dean and approval by the Academic Review Board.

#### Retrieved Context Chunks (Frozen Record)
The retrieved context was inspected to determine whether sufficient information about both attendance condonation and medical leave was retrieved:
1. **University Attendance Policy** > *Condonation of Attendance Shortage* (Similarity: **0.7719**)  
   `"Students with attendance between 65% and 74.9% may apply to the Dean of Academic Affairs for attendance condonation on genuine medical or compassionate grounds. The application must include an official medical certificate issued by a registered medical practitioner within seven working days of returning to campus, along with a nominal condonation fee. Condonation is granted at the sole discretion of the Academic Review Board."`
2. **Student Leave Regulations and Protocols** > *Medical Leave and Health Center Certification* (Similarity: **0.7601**)  
   `"In the event of severe illness or hospitalization, medical leave up to a maximum of 15 calendar days per semester may be recognized. The student or guardian must notify the Department Head within 48 hours of illness onset. Upon return, the student must report to the University Health Center for fitness verification with original hospital discharge summaries and medical prescriptions."`
3. **Student Leave Regulations and Protocols** > *Long-Term Semester Withdrawal* (Similarity: **0.6432**)  
   `"A student who experiences prolonged medical incapacitation requiring absence of more than four continuous weeks may petition the Academic Council for a formal Semester Withdrawal without academic penalty..."`

#### Actual Model Responses

- **Code Llama 7B**:
  > *"Based on the provided university policy context, medical leave cannot be used to condone attendance shortages. While students who experience severe illness or hospitalization can apply for medical leave up to a maximum of 15 calendar days per semester, this leave is not automatically applied towards attendance condonation. Instead, students with attendance between 65% and 74.9% may apply to the Dean of Academic Affairs for attendance condonation on genuine medical or compassionate grounds... However, it's important to note that the policy also states that the application must include an official medical certificate... Overall, the policies indicate that a student with 70% attendance can apply for attendance condonation on genuine medical or compassionate grounds, but the exact attendance percentage required for condonation is not specified."*

- **Phi-3 Mini**:
  > *"According to the retrieved University Attendance Policy, specifically under the section 'Condonation of Attendance Shortage,' a student with attendance between 65% and 74.9% may apply for attendance condonation for genuine medical or compassionate reasons... Given this policy, a student with 70% attendance seeking to address the shortage due to genuine medical grounds can apply for condonation but cannot use medical leave to address attendance shortage as the policies are distinctly separate. Medical leave concerns illness or hospitalization and offers a maximum of 15 calendar days per semester as indicated in the 'Student Leave Regulations and Protocols' section on Medical Leave and Health Center Certification. Therefore, the student should apply for attendance condonation as per the first policy or, alternatively, if their situation qualifies for a longer absence due to severe illness, they may apply for medical leave as per the second policy."*

- **Qwen 2.5 3B**:
  > *"According to the University Attendance Policy (Section: Condonation of Attendance Shortage), students with an attendance percentage between 65% and 74.9% can apply for attendance condonation due to genuine medical or compassionate grounds... In terms of medical leave, the Student Leave Regulations and Protocols (Section: Medical Leave and Health Center Certification) allow for up to 15 calendar days of medical leave per semester for severe illness or hospitalization... The student's current attendance of 70% does not align with the criteria for medical leave. Medical leave is intended for cases of severe illness or hospitalization, while attendance condonation is for genuine medical or compassionate grounds. The student should apply for attendance condonation as per the University Attendance Policy to address their 70% attendance."*

#### Analysis & Finding
- **Retrieval Quality**: Successful cross-document retrieval (captured Chunk 1 from Attendance Policy and Chunk 2 from Student Leave Regulations with high similarity >0.76).
- **Context Quality**: Both required rules were present in the prompt.
- **Model Behavior**: All three models recognized the distinction between medical leave and attendance condonation. However, Phi-3 Mini and Code Llama experienced generation looping/length inflation on this question, leading to Phi-3's 72-second latency outlier.

---

### 5.7 Case Studies Summary

| Case | Question ID | Category / Challenge | Retrieved Context | Actual Response Comparison | Primary Pipeline Finding |
|---|---|---|---|---|---|
| **Case 1** | **Q01** | Direct Factual (75% rule) | ✅ Exact match (0.9108) | All 3 models 100% correct | High semantic similarity leads to deterministic, reliable extraction across all models. |
| **Case 2** | **Q05** | Multi-Condition (70% + medical) | ✅ Condonation & debarment chunks | Phi-3 & Qwen correct; Code Llama contradicted itself | Retrieval success does not prevent generation failure when multiple constraints must be evaluated. |
| **Case 3** | **Q08** | Policy Waiver vs. Distractors | ⚠️ 1 relevant, 2 distractor chunks | Phi-3 & Qwen robust; Code Llama distracted | Models with lower instruction-following discipline incorporate irrelevant retrieved chunks into answers. |
| **Case 4** | **Q18** | Insufficient Context (Hostel) | ❌ Missing by design (~0.62 noise) | Phi-3 & Qwen stated missing; Code Llama hallucinated | Retrieval cannot verify information sufficiency; models must be evaluated on negative constraints. |
| **Case 5** | **Q20** | Multi-Document Synthesis | ✅ Chunks from two distinct policy docs | All 3 distinguished policies; caused latency spikes | Cross-document retrieval succeeded; prompt complexity led to output verbosity and latency outliers. |

---

### 5.8 Retrieval Quality → Context Quality → Response Quality

The RAG analysis demonstrates that the pipeline consists of three distinct stages that must be measured separately:

```text
Stage 1: Retrieval Quality (Did the search retrieve the expected policy section?)
       ↓
Stage 2: Context Quality (Did the combined retrieved chunks contain all necessary rules?)
       ↓
Stage 3: Response Quality (Did the LLM interpret and adhere strictly to the context?)
```

1. **Retrieval Quality (73.68%)**:
   - The vector search accurately retrieved the target section for 14 out of 19 answerable questions.
   - Failures at this stage occurred when questions contained terms with higher cosine similarity to general academic policies rather than specialized sections.

2. **Context Quality**:
   - Even when retrieval succeeded, fixed top-k ($k=3$) sometimes retrieved irrelevant distractor chunks (e.g., Q08).

3. **Response Quality**:
   - A model can receive the exact answer in its context but still hallucinate (e.g., Code Llama in Q05 claiming the condonation percentage is unspecified, or Q18 inventing university discretion).

### 5.9 Hallucination Analysis

The model evaluation demonstrated that hallucination occurs even in a RAG system:

| Model | Hallucination Rate |
|---|---|
| Code Llama 7B | 40% |
| Phi-3 Mini | 5% |
| Qwen 2.5 3B | 5% |

This proves that **retrieval alone does not eliminate hallucination**. Model architecture, instruction fine-tuning, and strict context adherence are decisive factors.

### 5.10 RAG Pipeline Conclusion

The evaluation demonstrates that RAG performance is an end-to-end pipeline problem:

```text
Question
   ↓
Retrieval Quality (73.68%)
   ↓
Context Quality (Sufficiency & Distractor Filtering)
   ↓
Generation Quality (Correctness: 85%–100%, Hallucination: 5%–40%)
   ↓
Final Response
```

Improving the system requires:
1. **Retrieval Optimization**: Hybrid search or similarity thresholding to avoid retrieving low-confidence distractor chunks (e.g., Q18).
2. **Model Selection**: Using instruction-tuned models with high grounding discipline (such as Qwen 2.5 3B or Phi-3 Mini) rather than larger, less grounded base models.

---

## Summary

Week 4 extended the University Knowledge Assistant from a functional RAG application into a thoroughly evaluated, evidence-based system.

The project now includes:

```text
20-question standardized evaluation dataset
        ↓
Frozen retrieval evaluation (73.68% quality)
        ↓
3-model controlled comparison
        ↓
Manual rubric scoring aggregated via score_results.py
        ↓
Response latency, token usage, and CPU/RSS measurements
        ↓
Case-by-case evidence-based RAG pipeline analysis
```

The evaluation confirms that:
- Model size does not correlate directly with RAG accuracy (Phi-3 Mini and Qwen 2.5 3B outperformed Code Llama 7B in both correctness and grounding).
- Qwen 2.5 3B delivered the best overall balance of high correctness (95%), perfect relevance (100%), minimal hallucination (5%), and the lowest latency (6.24 s).
- Retrieval quality (73.68%) is an independent architectural factor that bounds the information available to the generator.

Exercise 6 will address repository-level codebase understanding using the existing application.

---

# 6. Repository / Codebase Understanding

## 6.1 Objective

Exercise 6 investigated whether the existing University Knowledge Assistant could answer questions requiring understanding of multiple files, modules, and components in the application repository.

The existing LLM + RAG system was tested without modifying the application, retrieval pipeline, or knowledge base. This was intentionally done to evaluate the repository-level understanding capability of the system as it existed after Exercise 5.

## 6.2 Methodology

Six repository-level questions were submitted through the existing `/api/rag` endpoint using the same RAG pipeline developed in Week 3.

For each question, the following were examined:

1. The question submitted to the RAG system.
2. The retrieved context returned by the existing retrieval service.
3. The generated LLM response.
4. The actual repository implementation used as ground truth.

The repository source files used for verification were:

- `app/static/app.js` — frontend client logic
- `app/main.py` — application API
- `app/services/orchestrator.py` — multi-service orchestration
- `services/retrieval_service/main.py` — retrieval and cosine similarity
- `services/llm_service/main.py` — Ollama model interface
- `docker-compose.yml` — container and service networking configuration

## 6.3 Repository-Level Evaluation Results

| ID | Repository-Level Question | Result | Observed Behavior |
|---|---|---|---|
| Q1 | Trace a student question from the frontend through the application service, retrieval service, and LLM service. Which files are involved? | Failed | Generated a generic architecture description and did not identify the actual repository files. Retrieved context contained university policy documents. |
| Q2 | Which function in the application service calls the Retrieval Service, and what endpoint does it call? | Failed | Invented a nonexistent user-information endpoint instead of identifying `orchestrate_workflow()` and `POST /retrieve`. |
| Q3 | How does the Retrieval Service calculate similarity and select the top-k chunks? | Failed | Gave a generic explanation mentioning alternatives such as bag-of-words and Jaccard similarity. The actual implementation uses Ollama embeddings, pure-Python cosine similarity, descending sorting, and top-k selection. |
| Q4 | How does the LLM Service determine which Ollama model to use? | Failed | Gave a generic explanation of Ollama and did not identify the repository's model-selection logic. |
| Q5 | How does the Dockerized application communicate with Ollama running outside the containers? | Failed | Listed generic Docker networking possibilities instead of identifying `host.docker.internal`, `host-gateway`, and the actual Compose configuration. |
| Q6 | What happens if the Retrieval Service cannot be reached? | Failed | Returned irrelevant university attendance-policy information instead of identifying the application's connection-error handling. |

### 6.3.1 Quantitative Summary

- Repository-level questions tested: **6**
- Questions demonstrating reliable repository-level understanding: **0**
- Questions failing to demonstrate reliable repository-level understanding: **6**
- Observed success rate: **0/6 = 0%**

The result should be interpreted within the scope of this experiment. It does not mean that the underlying LLM or RAG pipeline is unusable for its intended university-policy question-answering task. It shows that the existing retrieval corpus does not support repository-level code understanding.

## 6.4 Ground-Truth Comparison

The actual repository contains the information required to answer the questions, but this information is not present in the RAG knowledge base.

For example, `app/services/orchestrator.py` contains the `orchestrate_workflow()` function. It sends an HTTP `POST` request to the Retrieval Service's `/retrieve` endpoint, constructs the context-augmented prompt, and then sends an HTTP `POST` request to the LLM Service's `/generate` endpoint.

Similarly, `services/retrieval_service/main.py` contains the `cosine_similarity()` implementation and the retrieval procedure that generates a query embedding, loads `knowledge_base.json`, calculates similarity for each chunk, sorts the results in descending order, and selects the requested top-k chunks.

The LLM Service implementation in `services/llm_service/main.py` determines the model using the request model when supplied, otherwise falling back to its configured default model. The default configuration resolves through `OLLAMA_MODEL`, `MODEL_NAME`, and finally `codellama:7b-instruct`.

**The Docker configuration** in `docker-compose.yml` explicitly maps `host.docker.internal` to `host-gateway` and uses `http://host.docker.internal:11434` for communication with Ollama running outside the containers.

None of this source-code information was retrieved during the repository-level tests.

## 6.5 Retrieval Limitation

The main limitation identified by the experiment is the mismatch between the question domain and the retrieval corpus.

The current knowledge base contains university policy documents such as attendance, examination, leave, and campus-facility policies. It does not contain the application's source-code files.

Therefore, when a repository-level question is submitted, the retrieval service still searches the policy corpus. The retrieved chunks are consequently unrelated to the requested source-code information.

This creates the following failure pattern:

```text
Repository-Level Question
        ↓
Existing RAG Retrieval
        ↓
University Policy Knowledge Base
        ↓
Irrelevant / Insufficient Context
        ↓
LLM
        ↓
Generic Answer / Incorrect Details / Hallucination
```
The experiment therefore demonstrates that retrieval quality is dependent not only on the similarity mechanism but also on whether the retrieval corpus contains the information required by the question.

## 6.6 Key Findings
Finding 1 — Domain-specific RAG does not provide repository understanding

The existing RAG pipeline performs retrieval over university-policy documents. It therefore supports the application's original domain but does not provide access to repository source code.

Finding 2 — Missing source-code context leads to unsupported answers

Several responses contained implementation details that were not present in the retrieved context and did not match the actual repository. Examples included an invented attendance-related API in Q2 and generic Docker networking options in Q5.

Finding 3 — The LLM cannot compensate reliably for missing repository context

Even though the underlying model has general programming knowledge, the experiment showed that it cannot be relied upon to reconstruct the specific implementation of this repository when the source code is absent from the retrieval corpus.

Finding 4 — Repository-level understanding requires repository-aware retrieval

To answer questions such as file tracing, function relationships, request flows, and component impact, the retrieval system would need access to source-code files and a retrieval strategy appropriate for code.

## 6.7 Exercise 6 Conclusion

Exercise 6 demonstrated a clear boundary of the existing University Knowledge Assistant.

The system can perform RAG over its university-policy knowledge base, but the same retrieval pipeline does not demonstrate reliable repository-level codebase understanding. All six repository-level questions failed to produce answers grounded in the actual source code.

This experiment establishes the need for a repository-aware retrieval layer if the system is later extended to answer questions about files, functions, modules, dependencies, and code flows.

Sourcegraph and more advanced repository-level code understanding techniques are covered in the following week's activity and were therefore not implemented as part of this exercise.
