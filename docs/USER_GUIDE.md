# MediChat RAG - User Guide

Welcome to MediChat RAG! This comprehensive guide will help you get the most out of the medical knowledge assistant.

Here is quick demo link of app: https://aqeel-awan2362-ai-engineer-portfolio-app-hhnsba.streamlit.app/

## Table of Contents

1. [Getting Started](#getting-started)
2. [Uploading Documents](#uploading-documents)
3. [Asking Questions](#asking-questions)
4. [Understanding Responses](#understanding-responses)
5. [Best Practices](#best-practices)
6. [Troubleshooting](#troubleshooting)
7. [FAQ](#faq)

---

## Getting Started

### What is MediChat RAG?

MediChat RAG is an AI-powered medical knowledge assistant that can:
- Answer questions from your uploaded medical documents
- Provide general medical information from its knowledge base
- Cite sources for document-based answers
- Maintain conversation context

### Important Disclaimer

⚠️ **This tool is for informational purposes only and is NOT a substitute for professional medical advice.** Always consult qualified healthcare providers for medical decisions.

### First Steps

1. **Open the Application**
   - Navigate to the application URL in your web browser
   - You should see the MediChat RAG interface with:
     - Document upload section (left sidebar)
     - Chat interface (main area)

2. **Decide Your Use Case**
   - **Option A**: Upload documents to ask specific questions about them
   - **Option B**: Use it as a general medical knowledge assistant without documents

---

## Uploading Documents

### Supported Formats

Currently supports: **PDF files only**

### How to Upload

1. **Locate the Upload Section**
   - Look for "📤 Document Upload" in the left sidebar

2. **Select Files**
   - Click "Choose PDF files" button
   - OR drag and drop PDF files into the upload area
   - You can select multiple files at once

3. **Process Documents**
   - After selecting files, click the "Process Documents" button
   - Wait for processing to complete (you'll see a spinner)
   - Success message will appear when ready

### What Happens During Processing?

```
Your PDF → Text Extraction → Text Chunking → 
Embedding Generation → Vector Storage → Ready for Questions!
```

**Processing Time**: Approximately 2-3 seconds per page

### Document Management

- **View Uploaded Documents**: Click "View Uploaded Documents" expander in sidebar
- **Document Information**: Shows filename and number of chunks created
- **Session-Based**: Documents are removed when you close the browser

### Tips for Better Results

- **Quality Matters**: Use clear, well-formatted PDFs
- **Size Limits**: No hard limit, but larger files take longer to process
- **Language**: English documents work best
- **Scanned PDFs**: Text-searchable PDFs work better than image-only scans

---

## Asking Questions

### Types of Questions

#### 1. Document-Specific Questions

Ask about content in your uploaded documents:

**Examples**:
- "What does my document say about diabetes treatment?"
- "Summarize the key findings in the uploaded file"
- "Does the document mention any side effects?"
- "What are the recommendations in my file?"

**Keywords that trigger document search**:
- "document", "file", "PDF"
- "mention", "mentioned"
- "in the document", "from my file"

#### 2. General Medical Questions

Ask about general medical knowledge (works with or without documents):

**Examples**:
- "What are the symptoms of hypertension?"
- "Explain how insulin works in the body"
- "What is the difference between type 1 and type 2 diabetes?"
- "How does the cardiovascular system function?"

#### 3. Conversational Interactions

The assistant handles natural conversation:

**Examples**:
- "Hi" / "Hello" → Greeting response
- "Thank you" → Acknowledgment
- "Goodbye" → Farewell message

### How to Ask Good Questions

✅ **DO**:
- Be specific and clear
- Ask one question at a time
- Provide context when needed
- Use complete sentences

❌ **DON'T**:
- Ask multiple unrelated questions at once
- Use unclear abbreviations
- Expect personal medical diagnoses
- Ask for emergency medical advice

### Question Examples by Category

#### Symptoms and Diagnosis
- "What are common symptoms of condition X?"
- "How is disease Y typically diagnosed?"
- "What tests are used to detect condition Z?"

#### Treatment and Medication
- "What are the treatment options for condition X?"
- "How does medication Y work?"
- "What are the side effects of drug Z?"

#### Prevention and Lifestyle
- "How can I prevent disease X?"
- "What lifestyle changes help with condition Y?"
- "What dietary recommendations exist for Z?"

#### Anatomy and Physiology
- "How does the X system work?"
- "What is the function of organ Y?"
- "Explain the process of Z"

---

## Understanding Responses

### Response Types

#### 1. Document-Based Answers

When documents are loaded and your question is document-related:

**Format**:
```
[Answer text based on your documents]

📚 View Sources:
- Document 1: filename.pdf (Chunk #3)
- Document 2: another_file.pdf (Chunk #7)
```

**What to do**:
- Read the main answer
- Click "View Sources" to see source excerpts
- Verify information against original documents

#### 2. General Knowledge Answers

When no documents are loaded or for general questions:

**Format**:
```
[Answer based on AI's general medical knowledge]
```

**What to know**:
- No source citations
- Based on training data (pre-existing knowledge)
- May include general disclaimers

#### 3. Clarification Requests

When your question is unclear:

**Format**:
```
"I'm not sure what you mean. Could you ask me a 
question about medical topics or your uploaded documents?"
```

**What to do**:
- Rephrase your question more clearly
- Add more context
- Break down complex questions

### Source Citations

#### Why Sources Matter
- Verify accuracy
- Trace information back to original documents
- Understand context

#### How to View Sources

1. Look for "📚 View Sources" under the answer
2. Click to expand the source list
3. Each source shows:
   - Document name
   - Chunk number
   - Excerpt preview (500 characters)

#### Source Example
```
📚 View Sources:

Document 1: Medical_Guidelines_2024.pdf (Chunk #5)
[Preview of the relevant text excerpt...]

Document 2: Treatment_Protocol.pdf (Chunk #12)
[Preview of the relevant text excerpt...]
```

---

## Best Practices

### For Best Results

1. **Upload Relevant Documents**
   - Use documents that contain the information you need
   - More documents ≠ better results (focus on quality)

2. **Ask Specific Questions**
   - ✅ "What does the document say about the three stages of treatment?"
   - ❌ "Tell me everything"

3. **Verify Important Information**
   - Check source citations
   - Cross-reference with original documents
   - Consult professionals for critical decisions

4. **Use Conversation Context**
   - Follow-up questions work well
   - Reference previous answers: "Can you elaborate on that?"

### Safety Guidelines

🚨 **Never use MediChat RAG for**:
- Emergency medical situations (call 911)
- Personal medical diagnosis
- Prescription decisions
- Replacing professional medical advice

✅ **Good use cases**:
- Learning about medical conditions
- Understanding medical documents
- Research and education
- General health information

### Privacy Considerations

- **Document Security**: Documents are processed in-memory and not permanently stored
- **Conversation Privacy**: Chats are session-based (deleted when you close the browser)
- **API Usage**: Text is sent to OpenAI API for processing
- **No Medical Records**: Don't upload actual patient medical records

---

## Troubleshooting

### Common Issues

#### 1. "Error processing [filename]"

**Possible Causes**:
- Corrupted PDF file
- Password-protected PDF
- Image-only PDF (no text)

**Solutions**:
- Try a different PDF
- Remove password protection
- Use OCR to convert scanned PDFs to text

#### 2. "Vector store not initialized"

**Cause**: Trying to ask document-specific questions without uploading documents

**Solution**: Upload and process documents first

#### 3. "I don't have enough information to answer that"

**Possible Reasons**:
- Question not covered in uploaded documents
- Question too vague
- Document processing incomplete

**Solutions**:
- Upload relevant documents
- Rephrase question more specifically
- Verify documents were processed successfully

#### 4. Slow Response Times

**Possible Causes**:
- Large documents
- Complex questions
- High API load

**Solutions**:
- Wait a few seconds
- Simplify your question
- Try again if it times out

#### 5. Irrelevant Answers

**Possible Causes**:
- Question ambiguity
- Limited document content
- Context misunderstanding

**Solutions**:
- Be more specific
- Provide more context
- Try rephrasing

### Getting Help

If issues persist:
- Check application logs (for developers)
- Contact support: ai.engineer.aqeel@gmail.com
- Report bugs via GitHub issues

---

## FAQ

### General Questions

**Q: Is MediChat RAG free to use?**  
A: Depends on deployment. Local use requires your own OpenAI API key (costs apply).

**Q: Can I use this for my patients?**  
A: Not recommended. This is an educational tool, not approved for clinical use.

**Q: How accurate are the responses?**  
A: Responses are generated by AI and should be verified. Accuracy depends on source documents and question clarity.

**Q: Is my data private?**  
A: Documents are processed in-memory (not saved). Text is sent to OpenAI API for processing.

### Document Questions

**Q: What file formats are supported?**  
A: Currently only PDF files.

**Q: How many documents can I upload?**  
A: No hard limit, but performance may degrade with many large documents.

**Q: Are documents saved permanently?**  
A: No, documents are removed when you close your browser session.

**Q: Can I delete individual documents?**  
A: Currently no. Refresh the page to clear all documents.

### Question & Answer

**Q: Why doesn't it answer from my document?**  
A: Ensure your question uses document-related keywords ("document says", "in my file", etc.).

**Q: Can it remember previous conversations?**  
A: Yes, within the same session. Closing the browser clears history.

**Q: How many follow-up questions can I ask?**  
A: No limit within a session (last 20 messages kept in context).

**Q: Can it summarize entire documents?**  
A: Yes, ask "Summarize my document" or "What are the main points?"

### Technical Questions

**Q: What AI model powers this?**  
A: OpenAI's GPT-3.5-turbo for text generation and text-embedding-ada-002 for embeddings.

**Q: How does the retrieval work?**  
A: Uses FAISS for vector similarity search on document embeddings.

**Q: Can I run this offline?**  
A: No, requires internet connection for OpenAI API access.

**Q: What are the system requirements?**  
A: Modern web browser, internet connection, that's it!

---

## Advanced Features

### Conversation Statistics

Find in the sidebar:
- Total messages exchanged
- Conversation duration
- Number of documents processed

### Export Chat History (Future Feature)

Coming soon:
- Export conversations as text
- Save for later reference
- Share with colleagues

---

## Tips & Tricks

### Power User Tips

1. **Chain Questions**: Build on previous answers
   ```
   You: "What are the symptoms of diabetes?"
   Bot: [Answers]
   You: "What causes those symptoms?"
   Bot: [Explains, understanding context]
   ```

2. **Comparative Questions**: 
   ```
   "Compare the treatments mentioned in documents 1 and 2"
   ```

3. **Specific Sections**:
   ```
   "What does page 5 say about treatment protocols?"
   ```

4. **Clarification Requests**:
   ```
   "Explain that in simpler terms"
   "Can you elaborate on the second point?"
   ```

### Shortcuts

- Press `Enter` to send message
- Use ↑/↓ arrows to navigate chat history
- Click document names in sources to see excerpts

---

## Providing Feedback

Your feedback helps improve MediChat RAG!

**Ways to provide feedback**:
- 👍/👎 buttons (if available)
- Email: ai.engineer.aqeel@gmail.com
- GitHub issues for bugs
- Feature requests welcome

---

## Additional Resources

- **Architecture Details**: See `docs/Architecture.md`
- **Deployment Guide**: See `docs/DEPLOYMENT.md`
- **API Documentation**: See OpenAI documentation
- **LangChain Docs**: [https://python.langchain.com](https://python.langchain.com)

---

**Document Version**: 1.0  
**Last Updated**: 2024  
**Author**: Muhammad Aqeel

**Happy Learning! 📚🏥**
