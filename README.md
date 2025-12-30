# zpdf

A PDF text extraction library written in Zig.

## Features

- Memory-mapped file reading for efficient large file handling
- Streaming text extraction (no intermediate allocations)
- Multiple decompression filters: FlateDecode, ASCII85, ASCIIHex, LZW, RunLength
- Font encoding support: WinAnsi, MacRoman, ToUnicode CMap
- XRef table and stream parsing (PDF 1.5+)
- Configurable error handling (strict or permissive)
- Multi-threaded parallel page extraction

## Benchmark

Text extraction performance vs MuPDF 1.26 (`mutool convert -F text`):

### Sequential

| Document | Pages | Size | zpdf | MuPDF | Speedup |
|----------|-------|------|------|-------|---------|
| [Adobe Acrobat Reference](https://helpx.adobe.com/pdf/acrobat_reference.pdf) | 651 | 19 MB | 137 ms | 530 ms | **3.9x** |
| [C++ Standard Draft](https://open-std.org/jtc1/sc22/wg21/docs/papers/2023/n4950.pdf) | 2,134 | 8 MB | 276 ms | 1,038 ms | **3.8x** |
| [Pandas Documentation](https://pandas.pydata.org/pandas-docs/version/1.4/pandas.pdf) | 3,743 | 15 MB | 447 ms | 1,216 ms | **2.7x** |
| [Intel SDM](https://cdrdv2.intel.com/v1/dl/getContent/671200) | 5,252 | 25 MB | 508 ms | 2,250 ms | **4.4x** |

### Parallel (multi-threaded)

| Document | Pages | Size | zpdf | MuPDF | Speedup |
|----------|-------|------|------|-------|---------|
| Adobe Acrobat Reference | 651 | 19 MB | 60 ms | 512 ms | **8.5x** |
| C++ Standard Draft | 2,134 | 8 MB | 142 ms | 1,020 ms | **7.2x** |
| Pandas Documentation | 3,743 | 15 MB | 233 ms | 1,204 ms | **5.2x** |
| Intel SDM | 5,252 | 25 MB | 127 ms | 2,260 ms | **18x** |

Peak throughput: **41,000 pages/sec** (Intel SDM, parallel)

Build with `zig build -Doptimize=ReleaseFast` for these results.

*Note: MuPDF's threading (`-T` flag) is for rendering/rasterization only. Text extraction via `mutool convert -F text` is single-threaded by design. zpdf parallelizes text extraction across pages.*

## Requirements

- Zig 0.15.2 or later

## Building

```bash
zig build              # Build library and CLI
zig build test         # Run tests
```

## Usage

### Library

```zig
const zpdf = @import("zpdf");

pub fn main() !void {
    var gpa = std.heap.GeneralPurposeAllocator(.{}){};
    defer _ = gpa.deinit();
    const allocator = gpa.allocator();

    const doc = try zpdf.Document.open(allocator, "file.pdf");
    defer doc.close();

    var buf: [4096]u8 = undefined;
    var writer = std.fs.File.stdout().writer(&buf);
    defer writer.interface.flush() catch {};

    for (0..doc.pages.items.len) |page_num| {
        try doc.extractText(page_num, &writer.interface);
    }
}
```

### CLI

```bash
zpdf extract document.pdf           # Extract all pages to stdout
zpdf extract -p 1-10 document.pdf   # Extract pages 1-10
zpdf extract -o out.txt document.pdf # Output to file
zpdf info document.pdf              # Show document info
zpdf bench document.pdf             # Run benchmark
```

## Project Structure

```
src/
├── root.zig         # Document API and core types
├── parser.zig       # PDF object parser
├── xref.zig         # XRef table/stream parsing
├── pagetree.zig     # Page tree resolution
├── decompress.zig   # Stream decompression filters
├── encoding.zig     # Font encoding and CMap parsing
├── interpreter.zig  # Content stream interpreter
├── simd.zig         # SIMD string operations
└── main.zig         # CLI
```

## Status

Implemented:
- XRef table and stream parsing
- Incremental PDF updates (follows /Prev chain for modified documents)
- Object parser
- Page tree resolution
- Content stream interpretation (Tj, TJ, Tm, Td, etc.)
- Font encoding (WinAnsi, MacRoman, ToUnicode CMap)
- CID font handling (Type0 composite fonts, Identity-H/V encoding, UTF-16BE)
- Stream decompression (FlateDecode, ASCII85, ASCIIHex, LZW, RunLength)

## License

MIT
