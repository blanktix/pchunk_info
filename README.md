# pchunk_info

pchunk_info is a simple tool for displaying basic information of PNG Chunk.

## Usage

For instances, you can check helper section by passing `-h` or `--help`.

```bash
$ python2 pchunk_info.py -h                         
usage: pchunk_info [-h] [--type chunk_type [chunk_type ...]] [--dump output]
                   [--extract] [--object id [id ...]] [--limit N] [--fix-crc]
                   file [file ...]

Simple pngchunk info based on list of chunk type

positional arguments:
  file                  a PNG image

optional arguments:
  -h, --help            show this help message and exit
  --type chunk_type [chunk_type ...], -t chunk_type [chunk_type ...]
                        Filter chunk by type
  --dump output, -d output
                        Dump raw chunk by selection
  --extract, -e         Extract chunk by selection
  --object id [id ...], -o id [id ...]
                        Filter chunk by object id
  --limit N             Number of chunk output
  --fix-crc             Fix CRC error and populate new image

                                                      
```

### Type-based filter

To specify the chunk type output based on its type, simply run:

```bash
# Single filter
$ python2 pchunk_info.py image.png -t 

# Multiple filter
$ python2 pchunk_info image.png -t IHDR IDAT

```

### Id-number Filter

To specify the chunk type output based on Id number, simply run:

```bash
# Single filter
$ python2 pchunk_info.py image.png -o 0

# Multiple filter
$ python2 pchunk_info image.png -o 0 1 2

# or using bash substitution
$ python2 pchunk_info image.png -o `seq 0 2`

```

### Limit output

To specify the number of chunk return, simply run:

```bash
# Show top 20 chunk
$ python2 pchunk_info.py image.png --limit 20

```

### Extract chunk by selection

To extract a certain section of PNG chunk, simply run:

```bash
# No filter
$ python2 pchunk_info.py image.png -e

# with filter
$ python2 pchunk_info.py image.png -t IDAT -e

```

### Dump PNG based on chunk selection

To dump PNG image based on selected chunk, simply run:

```bash
$ python2 pchunk_info.py image.png -d some_name.png

```

### Fix CRC error

To fix a CRC error issue, simply run:

```bash
$ python2 pchunk_info.py crc_error_example.png --fix-crc

```

## Demo

For instances, here is the demonstration of pchunk_info:

![Alt text](./demo.svg)

## Authors

* **hanasuru** - *Initial work* 

See also the list of [contributors](https://github.com/hanasuru/pchunk_info/contributors) who participated in this project.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details