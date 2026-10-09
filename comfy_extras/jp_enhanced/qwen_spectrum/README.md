Spectrum integration for the Japanese Qwen Image 2.1 nodes.

Source: https://github.com/awdqwdasdg/Comfyui-Spectrum-Qwen2.1
Revision: cfe1db560ae60132c261ab7df2cbc38ed5d0a528
License: MIT (see LICENSE).

The spectrum/ implementation is vendored. Local changes: remove the unused standalone patch entry point; copy captured features to avoid retaining a larger backing tensor. The integration creates and clears prediction state within each node execution, including failures.

Approximate acceleration can change image detail. Speed and quality on actual models have not been benchmarked. Start with the conservative defaults and compare with enabled=false at the same seed. GGUF uses the same native Qwen 2.1 core; actual model compatibility still needs runtime verification.

Registered nodes: Japanese text-to-image and image editing under `JP Enhanced/Qwen Image 2.1`. Both accept MODEL inputs from safetensors or GGUF loaders. Disable Spectrum to use the original generation path. Separate standard/GGUF aliases and non-Spectrum nodes have been removed.
