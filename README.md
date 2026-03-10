# Material Maker

This is a tool based on [Godot Engine](https://godotengine.org/) that can
be used to create textures procedurally and paint 3D models.

Its user interface is based on Godot's GraphEdit node: textures and brushes are
described as interconnected nodes.

![Screenshot](material_maker/doc/images/screenshot.png)

## Download

- **[Download on itch.io](https://rodzilla.itch.io/material-maker)**

On Windows, you can also install Material Maker using [Scoop](https://scoop.sh):

```text
scoop bucket add extras
scoop install material-maker
```
... or [Chocolatey](https://chocolatey.org/) (default or portable install):
```text
choco install material-maker
```
```text
choco install material-maker.portable
```

on MacOS, you can install Material Maker using [Homebrew](https://brew.sh/):

```text
brew install --cask material-maker
```

Can't wait for next release? Automated builds from master branch are available (use at your own risk):

<a href="https://github.com/RodZill4/material-maker/actions?query=branch%3Amaster">
    <img src="https://github.com/RodZill4/material-maker/workflows/dev-desktop-builds/badge.svg" alt="Build Passing" />
</a>

## Documentation

- **[User manual](https://rodzill4.github.io/material-maker/doc/)**

## Translations

Translation files can be installed using the **Install** button in the **Preferences** dialog.

- [Chinese translation](https://raw.githubusercontent.com/RodZill4/material-maker/f1be50b21a0f4991ac39e12a5362f5c5eb4c83a0/material_maker/locale/translations/zh.csv) (Created by **free_king**)

## MCP Integration (AI-Driven Material Creation)

This fork includes an MCP (Model Context Protocol) integration that lets AI assistants like Claude create and manipulate materials through natural language. It consists of:

- **GDScript addon** (`addons/material_maker_mcp/`) — TCP server that runs inside MM, exposing the node graph API
- **Python MCP server** (`mcp_server/`) — bridges MCP clients to the addon over TCP

See [`mcp_server/README.md`](mcp_server/README.md) for setup instructions and [`mcp_server/TOOLS.md`](mcp_server/TOOLS.md) for the full tool reference.

## Community

- **[Discord server](https://discord.gg/PF5V3mFwFM)**
- **[Material Maker subreddit](https://www.reddit.com/r/MaterialMaker/)**

## License

Copyright (c) 2018-present Rodolphe Suescun and contributors

Unless otherwise specified, files in this repository are licensed under the
MIT license. See [LICENSE.md](LICENSE.md) for more information.
