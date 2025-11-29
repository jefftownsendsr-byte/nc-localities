# Use conda miniconda base for reliable geospatial deps
FROM mambaorg/micromamba:1.4.0

# Create environment and set the working dir
ENV MAMBA_DOCKERFILE_ACTIVATE=1
ENV PATH=/opt/conda/bin:$PATH

WORKDIR /workspace

# Create and activate a conda environment with necessary packages
COPY environment.yml /workspace/environment.yml

RUN micromamba create -y -n nc-localities -f /workspace/environment.yml && \
    micromamba clean --all --yes

SHELL ["/bin/bash", "-lc"]

# Copy repository contents into image
COPY . /workspace

# Activate environment and set entrypoint
ENTRYPOINT ["/bin/bash", "-lc", "micromamba run -n nc-localities python scripts/build_nc_localities.py --output-dir /workspace/output --state 'North Carolina' --state-fips 37 --year 2025 --non-interactive --pack-output && micromamba run -n nc-localities python scripts/build_site.py --output-dir /workspace/output --year 2025"]
