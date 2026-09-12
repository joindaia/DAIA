# Third-party dependency licenses

The DAIA license applies to original project material. Dependencies retain their own licenses and notices; it does not relicense third-party code.

## Source release review

The installed Python core, MCP and test environment declares permissive licenses (MIT, BSD, Apache-2.0, PSF-2.0 and MIT-0), except certifi, which declares MPL-2.0. The optional PostgreSQL extra is not installed in this checked environment and must be reviewed before distributing a build that includes it.

The website lockfile declares the following licenses, including optional platform packages:

| License expression | Package entries |
| --- | ---: |
| 0BSD | 1 |
| Apache-2.0 | 16 |
| Apache-2.0 AND LGPL-3.0-or-later | 3 |
| Apache-2.0 AND LGPL-3.0-or-later AND MIT | 1 |
| BSD-2-Clause | 8 |
| BSD-3-Clause | 3 |
| BlueOak-1.0.0 | 3 |
| CC0-1.0 | 2 |
| ISC | 8 |
| LGPL-3.0-or-later | 10 |
| MIT | 217 |
| MPL-2.0 | 12 |
| Python-2.0 | 1 |

The LGPL entries are sharp/libvips image-processing dependencies; the MPL entries are lightningcss. They are build/runtime dependencies, not relicensed DAIA source. This source repository excludes node_modules, virtual environments and their binaries. Preserve their notices and satisfy their source/relinking requirements as applicable before shipping bundled binaries or containers.

This inventory is a metadata review of the pinned source-release dependencies. It does not certify every possible distribution or establish ownership of third-party material. New dependencies and copied source require review before inclusion.
