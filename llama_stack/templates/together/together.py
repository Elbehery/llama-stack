# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

from pathlib import Path

from llama_stack.apis.models import ModelType
from llama_stack.distribution.datatypes import (
    ModelInput,
    Provider,
    ShieldInput,
    ToolGroupInput,
)
from llama_stack.providers.inline.inference.sentence_transformers import (
    SentenceTransformersInferenceConfig,
)
from llama_stack.providers.inline.vector_io.faiss.config import FaissVectorIOConfig
from llama_stack.providers.remote.inference.together import TogetherImplConfig
from llama_stack.providers.remote.inference.together.models import MODEL_ENTRIES
from llama_stack.templates.template import (
    DistributionTemplate,
    RunConfigSettings,
    get_model_registry,
)


def get_distribution_template() -> DistributionTemplate:
    providers = {
        "inference": ["remote::together", "inline::sentence-transformers"],
        "vector_io": ["inline::faiss", "remote::chromadb", "remote::pgvector"],
        "safety": ["inline::llama-guard"],
        "agents": ["inline::meta-reference"],
        "telemetry": ["inline::meta-reference"],
        "eval": ["inline::meta-reference"],
        "datasetio": ["remote::huggingface", "inline::localfs"],
        "scoring": ["inline::basic", "inline::llm-as-judge", "inline::braintrust"],
        "tool_runtime": [
            "remote::brave-search",
            "remote::tavily-search",
            "inline::rag-runtime",
            "remote::model-context-protocol",
            "remote::wolfram-alpha",
        ],
    }
    name = "together"
    inference_provider = Provider(
        provider_id="together",
        provider_type="remote::together",
        config=TogetherImplConfig.sample_run_config(),
    )
    vector_io_provider = Provider(
        provider_id="faiss",
        provider_type="inline::faiss",
        config=FaissVectorIOConfig.sample_run_config(f"~/.llama/distributions/{name}"),
    )
    embedding_provider = Provider(
        provider_id="sentence-transformers",
        provider_type="inline::sentence-transformers",
        config=SentenceTransformersInferenceConfig.sample_run_config(),
    )
    available_models = {
        "together": MODEL_ENTRIES,
    }
    default_models = get_model_registry(available_models)
    default_tool_groups = [
        ToolGroupInput(
            toolgroup_id="builtin::websearch",
            provider_id="tavily-search",
        ),
        ToolGroupInput(
            toolgroup_id="builtin::rag",
            provider_id="rag-runtime",
        ),
        ToolGroupInput(
            toolgroup_id="builtin::wolfram_alpha",
            provider_id="wolfram-alpha",
        ),
    ]
    embedding_model = ModelInput(
        model_id="all-MiniLM-L6-v2",
        provider_id="sentence-transformers",
        model_type=ModelType.embedding,
        metadata={
            "embedding_dimension": 384,
        },
    )

    return DistributionTemplate(
        name=name,
        distro_type="self_hosted",
        description="Use Together.AI for running LLM inference",
        container_image=None,
        template_path=Path(__file__).parent / "doc_template.md",
        providers=providers,
        available_models_by_provider=available_models,
        run_configs={
            "run.yaml": RunConfigSettings(
                provider_overrides={
                    "inference": [inference_provider, embedding_provider],
                    "vector_io": [vector_io_provider],
                },
                default_models=default_models + [embedding_model],
                default_tool_groups=default_tool_groups,
                default_shields=[ShieldInput(shield_id="meta-llama/Llama-Guard-3-8B")],
            ),
            "run-with-safety.yaml": RunConfigSettings(
                provider_overrides={
                    "inference": [
                        inference_provider,
                        embedding_provider,
                    ],
                    "vector_io": [vector_io_provider],
                    "safety": [
                        Provider(
                            provider_id="llama-guard",
                            provider_type="inline::llama-guard",
                            config={},
                        ),
                        Provider(
                            provider_id="llama-guard-vision",
                            provider_type="inline::llama-guard",
                            config={},
                        ),
                        Provider(
                            provider_id="code-scanner",
                            provider_type="inline::code-scanner",
                            config={},
                        ),
                    ],
                },
                default_models=[
                    *default_models,
                    embedding_model,
                ],
                default_shields=[
                    ShieldInput(
                        shield_id="meta-llama/Llama-Guard-3-8B",
                        provider_id="llama-guard",
                    ),
                    ShieldInput(
                        shield_id="meta-llama/Llama-Guard-3-11B-Vision",
                        provider_id="llama-guard-vision",
                    ),
                    ShieldInput(
                        shield_id="CodeScanner",
                        provider_id="code-scanner",
                    ),
                ],
                default_tool_groups=default_tool_groups,
            ),
        },
        run_config_env_vars={
            "LLAMA_STACK_PORT": (
                "8321",
                "Port for the Llama Stack distribution server",
            ),
            "TOGETHER_API_KEY": (
                "",
                "Together.AI API Key",
            ),
        },
    )
