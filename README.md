# analyzePF

## What is analyzePF?

[analyzePF](https://github.com/noahrubin/analyzePF) is a command line tool for parsing information from Prefetch files taken from systems running Windows.  The tools was written to parse as much information from Prefetch files as possible in the most accurate way possible, and is written with the same four goals in mind as [analyzeMFT](https://github.com/noahrubin/analyzeMFT/tree/rewrite2018) (substituting Prefetch for Prefetch).

## Installation

This version of analyzePF is not yet available on PyPi, so it can be cloned via the following:

```bash
$ git clone git@github.com:noahrubin/analyzePF.git # (or https://github.com/noahrubin/analyzePF.git)
$ cd analyzePF
$ ./apf.py -h # show CLI usage
```

## Dependencies

All of the core dependencies beside [six](https://pypi.python.org/pypi/six) come shipped with analyzePF in the [lib/](https://github.com/noahrubin/analyzePF/tree/master/lib) directory, and the application uses those by default.  If there is a consensus that users want the ability to use already-installed versions of those packages (i.e. in a virtualenv), that change can be made easily.  Thus, the only potential dependencies are database drivers for SQLAlchemy to use.  See below:

| RDBMS Name | SQLAlchemy Link |
|------------|-----------------|
| SQLite | <a href="http://docs.sqlalchemy.org/en/latest/dialects/sqlite.html" target="_blank">http://docs.sqlalchemy.org/en/latest/dialects/sqlite.html</a> |
| PostgreSQL | <a href="http://docs.sqlalchemy.org/en/latest/dialects/postgresql.html" target="_blank">http://docs.sqlalchemy.org/en/latest/dialects/postgresql.html</a> |
| MySQL | <a href="http://docs.sqlalchemy.org/en/latest/dialects/mysql.html" target="_blank">http://docs.sqlalchemy.org/en/latest/dialects/mysql.html</a> |
| MSSQL | <a href="http://docs.sqlalchemy.org/en/latest/dialects/mssql.html" target="_blank">http://docs.sqlalchemy.org/en/latest/dialects/mssql.html</a> |
| Oracle | <a href="http://docs.sqlalchemy.org/en/latest/dialects/oracle.html" target="_blank">http://docs.sqlalchemy.org/en/latest/dialects/oracle.html</a> |

## Getting Started

analyzePF can output information into CSV, bodyfile, and JSON file formats, as well as into a relational database.  Which output format you want will determine the command to use. See the [Usage](#usage) section for full usage documentation.

#### CSV Output

```bash
$ ./apf.py parse csv summary -s /path/to/file-hash.pf -t /path/to/output.csv
```

```bash
$ ./apf.py parse csv summary -s /path/to/file-hash.pf -t /path/to/output.tsv --threads 3 --sep '    '
```

```bash
$ ./apf.py parse csv summary --lpath /path/to/log/ --lpref output -s /path/to/file-hash.pf -t /path/to/output.csv --threads 3
```

#### Bodyfile Output

```bash
$ ./apf.py parse body -s /path/to/file-hash.pf -t /path/to/output.body
```

```bash
$ ./apf.py parse body -s /path/to/file-hash.pf -t /path/to/output.body --threads 3
```

```bash
$ ./apf.py parse body --lpath /path/to/log/ --lpref output -s /path/to/file-hash.pf -t /path/to/output.body --threads 3
```

#### JSON Output

```bash
$ ./apf.py parse json -s /path/to/file-hash.pf -t /path/to/output.csv
```

```bash
$ ./apf.py parse json -s /path/to/file-hash.pf -t /path/to/output.tsv --threads 3 --sep '    '
```

```bash
$ ./apf.py parse json --lpath /path/to/log/ --lpref output -s /path/to/file-hash.pf -t /path/to/output.csv --threads 3
```

#### Database Output

```bash
$ ./apf.py parse db -s /path/to/file-hash.pf -n /path/to/output.db # SQLite by default
```

```bash
$ ./apf.py parse db -s /path/to/file-hash.pf -n testdb -C "postgres:passwd@localhost:5432" # PostgreSQL server running on localhost
```


```bash
$ ./apf.py parse db -s /path/to/file-hash.pf -n testdb -d postgresql -u postgres -p root -H localhost -P 5432 # Same as above
```

```bash
$ ./apf.py parse db -s /path/to/file-hash.pf -n testdb -C /path/to/config/file # Read connection string from file
```

## Usage

Much like [Git](https://git-scm.com/docs), the CLI for analyzePF is separated into directives.  See below for a detailed, hierarchical description of the directives.

### CLI Menu Root (apf.py -h)

| Directive | Description |
|-----------|-------------|
| parse | Prefetch file parser directives |
| query | Submit query to Prefetch database |

### Parse Menu (apf.py parse -h)

| Directive | Description |
|-----------|-------------|
| csv | Parse Prefetch file(s) to CSV |
| body | Parse Prefetch file(s) last execution times to bodyfile |
| json | Parse Prefetch file(s) to JSON |
| file | Parse Prefetch file(s) to multiple output formats (simultaneously) |
| db | Parse Prefetch file(s) to database |

#### Parse CSV Menu (apf.py parse csv -h)

| Argument | Flags | Optional | Description |
|-----------|------|----------|-------------|
| info_type | N/A | False | Type of information to output (choices: summary) |
| sources | -s, --source | False | Path to input file(s) - can use multiple times |
| target | -t, --target | False | Path to output file |
| help | -h, --help | True | Show help message and exit |
| log_path | --lpath | True | Path to log file directory (i.e. /path/to/logs or C:\Users\<user>\Documents\) |
| log_prefix | --lpref | True | Prefix for log file (default: apf_\<date\>) |
| threads | --threads | True | Number of processes to use |
| sep | -S, --sep | True | Output file separator (default: ",") |

#### Parse Body Menu (apf.py parse body -h)

| Argument | Flags | Optional | Description |
|-----------|------|----------|-------------|
| sources | -s, --source | False | Path to input file(s) - can use multiple times |
| target | -t, --target | False | Path to output file |
| help | -h, --help | True | Show help message and exit |
| log_path | --lpath | True | Path to log file directory (i.e. /path/to/logs or C:\Users\<user>\Documents\) |
| log_prefix | --lpref | True | Prefix for log file (default: apf_\<date\>) |
| threads | --threads | True | Number of processes to use |
| sep | -S, --sep | True | Output file separator (default: "\|") |

#### Parse JSON Menu (apf.py parse json -h)

| Argument | Flags | Optional | Description |
|-----------|------|----------|-------------|
| sources | -s, --source | False | Path to input file(s) - can use multiple times |
| target | -t, --target | False | Path to output file |
| help | -h, --help | True | Show help message and exit |
| log_path | --lpath | True | Path to log file directory (i.e. /path/to/logs or C:\Users\<user>\Documents\) |
| log_prefix | --lpref | True | Prefix for log file (default: apf_\<date\>) |
| threads | --threads | True | Number of processes to use |
| pretty | -p, --pretty | True | Whether to pretty-print the JSON output (ignored if threads > 1) |

#### Parse File Menu (apf.py parse file -h)

| Argument | Flags | Optional | Description |
|-----------|------|----------|-------------|
| sources | -s, --source | False | Path to input file(s) - can use multiple times |
| target | -t, --target | False | Path to output file (without extension) |
| formats | -f, --format | False | Comma-separated list of output formats (choices: csv, body, and json) |
| help | -h, --help | True | Show help message and exit |
| log_path | --lpath | True | Path to log file directory (i.e. /path/to/logs or C:\Users\<user>\Documents\) |
| log_prefix | --lpref | True | Prefix for log file (default: apf_\<date\>) |
| threads | --threads | True | Number of processes to use |
| pretty | -p, --pretty | True | Whether to pretty-print the JSON output (ignored if threads > 1) |
| info_type | -i, --info-type | True | Information type for CSV output |

#### Parse DB Menu (apf.py parse db -h)

| Argument | Flags | Optional | Description |
|-----------|------|----------|-------------|
| sources | -s, --source | False | Path to input file(s) - can use multiple times |
| db_name | -n, --db | False | Name of database to connect to (path to database if using sqlite) |
| help | -h, --help | True | Show help message and exit |
| db_conn_string | -C, --connect | True | Database connection string, or filepath to file containing connection string |
| db_driver | -d, --driver | True | Database driver to use (default: sqlite) |
| db_user | -u, --user | True | Name of database user (alternative to connection string) |
| db_passwd | -p, --passwd | True | Database user password (alternative to connection string) |
| db_host | -H, --host | True | Hostname or IP address of database (alternative to connection string) |
| db_port | -C, --connect | True | Port database is listening on (alternative to connection string) |
| log_path | --lpath | True | Path to log file directory (i.e. /path/to/logs or C:\Users\<user>\Documents\) |
| log_prefix | --lpref | True | Prefix for log file (default: apf_\<date\>) |
| threads | --threads | True | Number of processes to use |

For examples, see [Getting Started](#getting-started)

### Query Menu (apf.py query -h)

| Argument | Flags | Optional | Description |
|-----------|------|----------|-------------|
| query | -q, --query | False | Query to submit to database |
| db_name | -n, --db | False | Name of database to connect to (path to database if using sqlite) |
| help | -h, --help | True | Show help message and exit |
| db_conn_string | -C, --connect | True | Database connection string, or filepath to file containing connection string |
| db_driver | -d, --driver | True | Database driver to use (default: sqlite) |
| db_user | -u, --user | True | Name of database user (alternative to connection string) |
| db_passwd | -p, --passwd | True | Database user password (alternative to connection string) |
| db_host | -H, --host | True | Hostname or IP address of database (alternative to connection string) |
| db_port | -C, --connect | True | Port database is listening on (alternative to connection string) |
| log_path | --lpath | True | Path to log file directory (i.e. /path/to/logs or C:\Users\<user>\Documents\) |
| log_prefix | --lpref | True | Prefix for log file (default: apf_\<date\>) |
| target | -t, --target | True | Path to output file (default: stdout) |
| sep | -S, --sep | True | Output file separator (default: ",") |
| title | -T, --title | True | Title to use for output table |

Example:

```bash
$ ./apf.py query -n ./test.db -q "select file_name, file_path, sha2hash from fileledger"
```

## Output Formats

Due to the relational nature of the Prefetch, the various file formats output different types of information.  See the sections below for a detailed desciption of each.

### CSV Format

| Field | Description |
|-------|-------------|
| Version | See [src/structures/prefetch](https://github.com/noahrubin/analyzePF/blob/master/src/structures/prefetch.py) (PrefetchVersion) |
| Signature | See [src/structures/prefetch](https://github.com/noahrubin/analyzePF/blob/master/src/structures/prefetch.py) (PrefetchHeader) |
| ExecutableName | See [src/structures/prefetch](https://github.com/noahrubin/analyzePF/blob/master/src/structures/prefetch.py) (PrefetchHeader) |
| PrefetchHash | See [src/structures/prefetch](https://github.com/noahrubin/analyzePF/blob/master/src/structures/prefetch.py) (PrefetchHeader) |
| SectionAEntriesCount | See [src/structures/prefetch](https://github.com/noahrubin/analyzePF/blob/master/src/structures/prefetch.py) (PrefetchFileInformation*) |
| SectionBEntriesCount | See [src/structures/prefetch](https://github.com/noahrubin/analyzePF/blob/master/src/structures/prefetch.py) (PrefetchFileInformation*) |
| SectionCLength | See [src/structures/prefetch](https://github.com/noahrubin/analyzePF/blob/master/src/structures/prefetch.py) (PrefetchFileInformation*) |
| SectionDEntriesCount | See [src/structures/prefetch](https://github.com/noahrubin/analyzePF/blob/master/src/structures/prefetch.py) (PrefetchFileInformation*) |
| LastExecutionTime | Most recent last execution time entry |
| ExecutionCount | See [src/structures/prefetch](https://github.com/noahrubin/analyzePF/blob/master/src/structures/prefetch.py) (PrefetchFileInformation*) |
| VolumeDevicePath | "\|"-separated list of volume device paths (see [src/structures/prefetch](https://github.com/noahrubin/analyzePF/blob/master/src/structures/prefetch.py) - PrefetchVolumeInformation*) |
| VolumeCreateTime | "\|"-separated list of volume create times (see [src/structures/prefetch](https://github.com/noahrubin/analyzePF/blob/master/src/structures/prefetch.py) - PrefetchVolumeInformation*) |
| VolumeSerialNumber | "\|"-separated list of volume serial numbers (see [src/structures/prefetch](https://github.com/noahrubin/analyzePF/blob/master/src/structures/prefetch.py) - PrefetchVolumeInformation*) |
| FileMetricsArrayCount | Count of file metrics entries (see [src/structures/prefetch](https://github.com/noahrubin/analyzePF/blob/master/src/structures/prefetch.py) - PrefetchFileMetricsEntry*) |
| TraceChainArrayCount | Count of trace chain entries (see [src/structures/prefetch](https://github.com/noahrubin/analyzePF/blob/master/src/structures/prefetch.py) - PrefetchTraceChainEntry) |
| FileReferenceCount | Count of $MFT file References (see [src/structures/prefetch](https://github.com/noahrubin/analyzePF/blob/master/src/structures/prefetch.py) - PrefetchFileReferences) |
| DirectoryStringsCount | Count of directory strings (associated with volume information entry) |
| FileNameStrings | "\|"-separated list of filename strings (associated with file metrics entry) |

### Bodyfile Format

The body format attempts to mimic the bodyfile format v3.x created by [TSK](http://wiki.sleuthkit.org/index.php?title=Body_file):

| Field | Description |
|-------|-------------|
| nodeidx | index of parsed Prefetch |
| recordidx | NULL |
| MD5 | NULL |
| name | filename of parsed Prefetch file |
| inode | FULL |
| mode_as_string | FULL |
| UID | FULL |
| GID | 'LET' (Last Execution Time) |
| size | size of parsed Prefetch file |
| atime | last execution timestamp |
| mtime | NULL |
| ctime | NULL |
| crtime | NULL |

\*: the nodeidx field exists so that when processing data in parallel, the program knows how to properly sort output data.

## JSON Format

The JSON format is an unordered collection of data parsed from each Prefetch entry, and contains the following top-level keys:

| Key Name | Description |
|----------|-------------|
| header | See [src/structures/prefetch](https://github.com/noahrubin/analyzePF/blob/master/src/structures/prefetch.py) (PrefetchHeader)|
| file_info | See [src/structures/prefetch](https://github.com/noahrubin/analyzePF/blob/master/src/structures/prefetch.py) (PrefetchFileInformation*) |
| file_metrics | See [src/structures/prefetch](https://github.com/noahrubin/analyzePF/blob/master/src/structures/prefetch.py) (PrefetchFileMetrics*) |
| filename_strings | List of filenames associated with file metrics array entries |
| trace_chains | See [src/structures/prefetch](https://github.com/noahrubin/analyzePF/blob/master/src/structures/prefetch.py) (PrefetchTraceChainEntry) |
| volumes_info | See [src/structures/prefetch](https://github.com/noahrubin/analyzePF/blob/master/src/structures/prefetch.py) (PrefetchVolumeInformation*) |
| file_references | See [src/structures/prefetch](https://github.com/noahrubin/analyzePF/blob/master/src/structures/prefetch.py) (PrefetchFileReferences) |
| directory_strings | List of lists of directory strings associated with volumes information array entries |

## DB Format

See [src/database/models.py](https://github.com/noahrubin/analyzePF/blob/master/src/database/models.py).

## Contributing/Suggestions

analyzePF is the second in a set of tools I intend on writing to parse forensic artifacts pertinent to DFIR with the [aforementioned](#what-is-analyzepf) four goals in mind.  Writing these parsers is my way of aiding in the democratization of DFIR, reducing the need for expensive licenses to solve cases.  To that end, any and all help/suggestions are welcome! Please open an issue if you find a bug or have a feature request, or please reach out to me at adfir [at] sudomail [dot] com with any comments!

## Resources


\#\#TODO
