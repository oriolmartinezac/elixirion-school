# TAGS for resulting building image
PREFIX           := oriolmac
COMPSS_VERSION   := 3.3
MIN_BASE_TAG     := min_base
FULL_BASE_TAG    := full_base
COMPSS_TAG       := compss_heuristics
DEBUG_TAG        := compss_debug
BUILDER          := compss-builder
PLATFORMS        := amd64 arm64
NAMESPACE        := buildkit

# Check if the system architecture is arm
ifeq ($(shell uname -m),aarch64)
	ARCH_TAG=arm
endif

define arch_ready =
$(shell kubectl get nodes -l kubernetes.io/arch=$(1) --no-headers 2>/dev/null \
        | awk '$$2=="Ready"{print "yes"; exit}')
endef

# Check if running in Kubernetes environment
KUBE_AVAILABLE := $(shell kubectl get nodes >/dev/null 2>&1 && echo "true" || echo "false")

.PHONY: help all clean 

help:
	@echo "Available targets:"
	@echo "  help         - Show this help message"
	@echo "  prepare      - Prepare the environment for building."
	@echo "  clean        - Remove builders"
	@echo ""
	@echo "Environment detected:"
	@echo "  Kubernetes available: $(KUBE_AVAILABLE)"
	@echo "  Architecture: $$(uname -m)"
	@echo ""
	@echo "Note: The default target is 'app'."


# -----------------------[ DEFAULT ]----------------------
all: prepare

prepare:
ifeq ($(KUBE_AVAILABLE),true)
	@echo "Kubernetes available, using kubernetes-container driver"

	# Ensure namespace exists
	@if ! kubectl get namespace $(NAMESPACE) >/dev/null 2>&1; then \
		echo "Creating namespace $(NAMESPACE)"; \
		kubectl create namespace $(NAMESPACE); \
	else \
		echo "Namespace $(NAMESPACE) already exists"; \
	fi

	@if [ "$(call arch_ready,amd64)" = "yes" ]; then \
		if docker buildx inspect kube-builder >/dev/null 2>&1 ; then \
			echo "Appending amd64 node to existing builder"; \
			docker buildx create --append --name kube-builder \
				--platform=linux/amd64 \
				--driver kubernetes \
				--driver-opt=namespace=$(NAMESPACE),nodeselector=kubernetes.io/arch=amd64 \
				--node kube-builder-amd64 ; \
		else \
			echo "Creating builder with first Ready arch = amd64"; \
			docker buildx create --name kube-builder --bootstrap \
				--driver kubernetes \
				--platform=linux/amd64 \
				--driver-opt=namespace=$(NAMESPACE),nodeselector=kubernetes.io/arch=amd64 \
				--node kube-builder-amd64 ; \
		fi; \
	else \
		echo "Skipping amd64: no Ready nodes"; \
	fi

	@if [ "$(call arch_ready,arm64)" = "yes" ]; then \
		if docker buildx inspect kube-builder >/dev/null 2>&1 ; then \
			echo "Appending arm64 node to existing builder"; \
			docker buildx create --append --name kube-builder \
				--platform=linux/arm64 \
				--driver kubernetes \
				--driver-opt=namespace=$(NAMESPACE),nodeselector=kubernetes.io/arch=arm64 \
				--node kube-builder-arm64 ; \
		else \
			echo "Creating builder with first Ready arch = arm64"; \
			docker buildx create --name kube-builder --bootstrap \
				--driver kubernetes \
				--platform=linux/arm64 \
				--driver-opt=namespace=$(NAMESPACE),nodeselector=kubernetes.io/arch=arm64 \
				--node kube-builder-arm64 ; \
		fi; \
	else \
		echo "Skipping arm64: no Ready nodes"; \
	fi

	docker buildx use kube-builder
	docker buildx inspect kube-builder --bootstrap

endif

## Clean environment
clean:
	-docker buildx rm kube-builder
	-kubectl delete deployment -l app=kube-builder-arm64 -n $(NAMESPACE) --ignore-not-found
	@echo "Installation environment cleaned"
