import json
import random
from pathlib import Path


OUTPUT_PATH = Path(
    "data/evaluation/expanded_evaluation_dataset.json"
)

random.seed(42)


INCIDENT_TEMPLATES = [
    {
        "root_cause": "Connection pool exhaustion",
        "services": [
            "PaymentService",
            "BillingService",
            "CheckoutService",
            "OrderService",
            "SubscriptionService",
        ],
        "exception": "ConnectionPoolExhaustedError",
        "message": "No available database connections",
        "log_signal": "Connection pool exhausted",
        "operation": "process_request",
        "file": "database/connection_pool.py",
        "function": "acquire",
    },
    {
        "root_cause": "API request timeout",
        "services": [
            "OrderService",
            "InventoryService",
            "CheckoutService",
            "ShippingService",
            "CatalogService",
        ],
        "exception": "RequestTimeoutError",
        "message": "Request timeout after 3000ms",
        "log_signal": "Request timeout after 3000ms",
        "operation": "call_dependency",
        "file": "clients/http_client.py",
        "function": "request",
    },
    {
        "root_cause": "Authentication failure",
        "services": [
            "AuthService",
            "LoginService",
            "UserService",
            "GatewayService",
            "IdentityService",
        ],
        "exception": "AuthenticationError",
        "message": "Invalid credentials",
        "log_signal": "Authentication failed: invalid credentials",
        "operation": "authenticate",
        "file": "clients/identity_client.py",
        "function": "request_token",
    },
    {
        "root_cause": "Memory exhaustion",
        "services": [
            "RecommendationService",
            "AnalyticsService",
            "ReportingService",
            "SearchService",
            "DataProcessingService",
        ],
        "exception": "java.lang.OutOfMemoryError",
        "message": "Java heap space",
        "log_signal": "Java heap space exhausted",
        "operation": "generate",
        "file": "FeatureBuilder.java",
        "function": "buildMatrix",
    },
    {
        "root_cause": "Null pointer failure",
        "services": [
            "UserService",
            "ProfileService",
            "OrderService",
            "CatalogService",
            "PreferenceService",
        ],
        "exception": "java.lang.NullPointerException",
        "message": "Cannot invoke method because object is null",
        "log_signal": "NullPointerException while processing request",
        "operation": "process_request",
        "file": "ProfileProcessor.java",
        "function": "processPreferences",
    },
    {
        "root_cause": "Network connectivity failure",
        "services": [
            "GatewayService",
            "PaymentService",
            "OrderService",
            "NotificationService",
            "ShippingService",
        ],
        "exception": "NetworkConnectivityError",
        "message": "Connection refused",
        "log_signal": "Connection refused by remote host",
        "operation": "connect",
        "file": "network/client.py",
        "function": "connect",
    },
    {
        "root_cause": "Storage failure",
        "services": [
            "FileService",
            "UploadService",
            "ReportService",
            "MediaService",
            "BackupService",
        ],
        "exception": "StorageFullError",
        "message": "No space left on device",
        "log_signal": "Disk full: no space left",
        "operation": "write_file",
        "file": "storage/file_writer.py",
        "function": "write",
    },
    {
        "root_cause": "Cache failure",
        "services": [
            "ProductService",
            "SessionService",
            "RecommendationService",
            "CatalogService",
            "UserService",
        ],
        "exception": "CacheConnectionError",
        "message": "Unable to connect to cache server",
        "log_signal": "Cache connection failed",
        "operation": "get_cached_value",
        "file": "cache/redis_client.py",
        "function": "get",
    },
    {
        "root_cause": "Kafka failure",
        "services": [
            "OrderService",
            "PaymentService",
            "NotificationService",
            "EventService",
            "AnalyticsService",
        ],
        "exception": "KafkaProducerError",
        "message": "Failed to publish message",
        "log_signal": "Kafka message publish failed",
        "operation": "publish_event",
        "file": "messaging/kafka_producer.py",
        "function": "send",
    },
    {
        "root_cause": "Configuration failure",
        "services": [
            "PaymentService",
            "OrderService",
            "AuthService",
            "GatewayService",
            "NotificationService",
        ],
        "exception": "ConfigurationError",
        "message": "Required configuration value is missing",
        "log_signal": "Missing required configuration",
        "operation": "initialize",
        "file": "config/application_config.py",
        "function": "load",
    },
]


def build_incident(case_id: int, template: dict) -> dict:
    service = random.choice(template["services"])

    user_id = f"USER-{random.randint(1000, 9999)}"
    request_id = f"REQ-{random.randint(10000, 99999)}"

    line_number = random.randint(50, 250)

    query = (
        f"What caused the {service} failure "
        f"for request {request_id}?"
    )

    # The synthetic stacktrace generator uses different
    # frame layouts for Python and Java incidents.
    if template["file"].endswith(".java"):
        evidence_line = line_number
    else:
        evidence_line = line_number + 5

    return {
        "incident_id": f"synthetic_{case_id:03d}",
        "query": query,
        "ground_truth_root_cause": template["root_cause"],
        "relevant_evidence": [
            "incident.log:line 4",
            "incident.stacktrace:exception",
            (
                f"incident.stacktrace:"
                f"{template['file']}:{evidence_line}"
            ),
        ],
        "metadata": {
            "service": service,
            "user_id": user_id,
            "request_id": request_id,
            "exception": template["exception"],
            "exception_message": template["message"],
            "log_signal": template["log_signal"],
            "operation": template["operation"],
            "file": template["file"],
            "function": template["function"],
            "line": line_number,
        },
    }

def main():
    dataset = []

    cases_per_category = 5

    case_id = 1

    for template in INCIDENT_TEMPLATES:
        for _ in range(cases_per_category):
            dataset.append(
                build_incident(
                    case_id,
                    template,
                )
            )

            case_id += 1

    output = {
        "description": (
            "Synthetic TraceAI evaluation dataset "
            "generated from deterministic incident templates."
        ),
        "seed": 42,
        "total_cases": len(dataset),
        "categories": len(INCIDENT_TEMPLATES),
        "cases_per_category": cases_per_category,
        "cases": dataset,
    }

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        OUTPUT_PATH,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            output,
            file,
            indent=2,
        )

    print("=" * 70)
    print("TRACEAI SYNTHETIC EVALUATION DATASET")
    print("=" * 70)
    print(f"Output       : {OUTPUT_PATH}")
    print(f"Categories   : {len(INCIDENT_TEMPLATES)}")
    print(f"Cases        : {len(dataset)}")
    print(f"Cases/category: {cases_per_category}")
    print("Seed         : 42")
    print("=" * 70)

    print("\nCategories:")

    for template in INCIDENT_TEMPLATES:
        print(
            f"- {template['root_cause']}"
        )


if __name__ == "__main__":
    main()