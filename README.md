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

| Document | Pages | zpdf | MuPDF | Speedup |
|----------|-------|------|-------|---------|
| [Adobe Acrobat Reference](https://helpx.adobe.com/pdf/acrobat_reference.pdf) | 651 | 123 ms | 511 ms | **4.2x** |
| [Pandas Documentation](https://pandas.pydata.org/pandas-docs/version/1.4/pandas.pdf) | 3,743 | 402 ms | 1,107 ms | **2.8x** |
| Adobe 10x (merged) | 6,510 | 730 ms | 2,950 ms | **4.0x** |

### Parallel (multi-threaded)

| Document | Pages | zpdf | MuPDF | Speedup |
|----------|-------|------|-------|---------|
| Adobe Acrobat Reference | 651 | 57 ms | 482 ms | **8.4x** |
| Pandas Documentation | 3,743 | 215 ms | 1,109 ms | **5.2x** |
| Adobe 10x (merged) | 6,510 | 127 ms | 2,935 ms | **23x** |

Peak throughput: **51,142 pages/sec** (Adobe 10x, parallel)

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
