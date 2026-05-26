# AI-Powered Invoice Automation

## Overview

This project is an end-to-end automation workflow designed to streamline accounts payable by automatically processing emailed invoices, extracting structured data, and syncing it with financial systems.

## Problem Statement

Manual invoice entry is slow, prone to human error, and difficult to scale. Businesses often deal with a variety of invoice formats (PDFs, images, scans) that traditional template-based OCR cannot handle reliably.

## Architecture

1. **Trigger**: An n8n workflow monitors a dedicated email inbox for new messages with attachments.
2. **Extraction Service**: A FastAPI service receives the invoice file and uses a Vision-Language Model (VLM) to extract structured JSON data.
3. **Validation**: A logic layer checks for missing fields (Invoice #, Date, Total, Tax) and validates the math.
4. **Exception Handling**: Invoices that fail validation are routed to a human-in-the-loop queue.
5. **Output**: Validated data is pushed to a database or accounting software API.

## Key Technical Decisions

- **VLM over OCR**: Chose VLMs for extraction because they can understand the context of an invoice regardless of the layout, eliminating the need for brittle, coordinate-based templates.
- **n8n for Orchestration**: Selected for its visual workflow builder and easy integration with email servers and external APIs.
- **FastAPI for Inference**: Provides a high-performance, asynchronous wrapper around the extraction model.

## Implementation Details

- **Field Extraction**: The model is prompted to extract `vendor_name`, `date`, `total_amount`, `currency`, and `line_items`.
- **Confidence Scoring**: The extraction service returns a confidence score; anything below 0.8 triggers a manual review.

## Challenges & Solutions

- **Multi-page Invoices**: Handled by processing each page and merging the line items in a final synthesis step.
- **Low-Quality Scans**: Improved accuracy by applying a pre-processing contrast-enhancement step using OpenCV before sending the image to the VLM.

## Tech Stack

- **Orchestration**: n8n
- **Backend**: FastAPI, Python
- **AI**: Vision-Language Model (Llama 4 Scout)
- **Deployment**: Docker, Azure

## Results & Outcomes

Reduced invoice processing time from an average of 5 minutes per invoice to under 30 seconds, with a 95%+ accuracy rate on clear digital PDFs.

## FAQ

**Q: How does the system handle invoices from new vendors?**
A: Since the system uses a general-purpose Vision-Language Model instead of templates, it can process invoices from vendors it has never seen before with high accuracy.

**Q: What happens if the extraction is wrong?**
A: We have a validation layer that cross-checks line items against the total amount. If the math doesn't add up, the invoice is flagged for manual review.

**Q: Is it secure?**
A: Yes, the system can be deployed entirely within a private VPC, and data is only processed for extraction without being stored in the model's training set.
