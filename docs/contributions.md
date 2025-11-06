# Contributions

Contributions to the Jobstats platform and its tools are welcome. To work with the code, build a Conda environment:

```
$ conda create --name jobstats-dev requests blessed ruff pytest-mock mkdocs-material -c conda-forge
```

Be sure that the tests are passing before making a pull request:

```
(jobstats-dev) $ pytest
```

## List of Contributors

- Anish Chanda, Iowa State University, provided the option of using an [external MariaDB database](./setup/external-database.md) to store the job summary statistics.
