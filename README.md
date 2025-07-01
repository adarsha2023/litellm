# LiteLLM with Google Spanner & Gemini Integration

A production-ready LiteLLM proxy server with Google Cloud Spanner for token management and Gemini AI integration, optimized for Red Hat Enterprise Linux.

[![CI](https://github.com/yourusername/litellm-spanner-gemini/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/litellm-spanner-gemini/actions/workflows/ci.yml)
[![Security](https://github.com/yourusername/litellm-spanner-gemini/actions/workflows/security.yml/badge.svg)](https://github.com/yourusername/litellm-spanner-gemini/actions/workflows/security.yml)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## Features

- 🚀 **Production Ready**: Systemd service, logging, monitoring
- 🔐 **Secure Token Management**: Google Spanner backend with encryption
- 🤖 **Gemini Integration**: Full support for all Gemini models
- 📊 **Usage Tracking**: Comprehensive analytics and cost monitoring
- 🔄 **Auto-scaling**: Load balancing and failover support
- 🐳 **Containerized**: Docker and Kubernetes ready
- 🏗️ **Infrastructure as Code**: Terraform modules included

## Quick Start

### Prerequisites
- Red Hat Enterprise Linux 8+
- Python 3.13
- Google Cloud Project with billing enabled
- Gemini API key

### Installation
```bash
git clone https://github.com/yourusername/litellm-spanner-gemini.git
cd litellm-spanner-gemini
chmod +x scripts/install.sh
./scripts/install.sh
