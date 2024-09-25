# Workspace Design

Ultimately, Flora should be a modding tool. And to effectively mod Professor Layton (or possibly any other DS game), you'll
need to work with an extracted file system. Then you need to keep track of which files you want to add/remove, which to change,
and how to repack all of this into a ROM without auxiliary decompressed files getting mixed in.

This is where Flora could shine, by managing the entire process for the user! It could automatically extract a ROM (and all
nested archives inside it) into a workspace folder, track which ones those are (and test them for validity against a known
official list of checksums), keep track of changes (allowing the user to manually add/remove files), and finally repack with a
single command!

## Structure

The `data/dwc/ftc` structure would probably be preserved, since those could technically also be manipulated by the user (though
for manipulating `arm9.bin` for example, Flora should have easier & more sophisticated patching methods). Other than that,
initial folder structure should be entirely preserved.

Certain (most) files won't be usefully inspectable on a regular computer without special tools; these files could be left in
the directory as they are, and maybe that should be the case for a copy of them, but Flora should also make a best effort to
convert them into a human-readable (and editable) format.

When doing this, let's say for the archive file `test.arc`, we decompress the archive & need to somehow know what file type
lies beneath it (for official files this can be common knowledge to lookup, for custom files the user might have to specify).
Once it has been determined that the file is internally, let's say a BGX image, then the resulting file would be saved as
`test{arc}.bgx`.

This naming convention of appending a conversion step in curly braces (before the file ending) can be used in all places: when
extracting PCM archives, which may contain lots of files, the result could be a folder called `archive{pcm}` to indicate that
its contents were extracted from, and need to be repacked into, a PCM file. This doesn't just apply to extraction either: in
a second step, the `test{arc}.bgx` file from above could be further transformed into an indexed-palette PNG file, called
`test{arc}{bgx}.png`.

This convention was chosen, because it is unlikely to collide with any real game file paths. If however that were to ever
happen, by a file path in a game containing the curly braces characters, those paths would need to be "escaped" by doubling up
any instance of them. ie. `realgamefile{TXT}` would convert to `realgamefile{{TXT}}` in the base folder structure.

Obviously user-made files should follow this convention as well, immediately giving Flora good information about what to do
with each newly added file. But perhaps this is more of a default & can be overridden when checking in a file.

## Checkin

Flora should keep track of which files belong to the final game, as oppposed to being auxiliary formats or decompressed data.
That information is just a list of filenames relative to the workspace, which could be stored in a `.flora` directory in the
workspace root, and accessed through the Flora CLI.

When extracting a game using Flora, all extracted files and subfiles should automatically be checked in. However the user can
use the CLI to manually checkin custom files that should be added to the ROM, as well as un-checkin original files that
should be deleted.

In case the game files were extracted by a program other than Flora, it is also possible to run a command to automatically
checkin all the files of the workspace one time. Note that, once this comprehensive un- and repacking functionality exists,
we wouldn't recommend working around it since this would also break the conversion naming convention.

What's checked-in on the user side is the final conversion result file, not the original raw filename. Flora has enough
information from that to incrementally pack files together as they should be; eg. in an `archive{pcm}` folder each individual
`file{loc}.txt` has to be checked in (to allow adding/removing files from archives as well), but not the `archive.pcm` itself:
Flora will realize that all the collected `file.loc` files need to be collected and then the folder packed into a PCM archive.

In the event that a file is checked-in, but doesn't exist, the `pack` function should display this as an error, and possibly ask
the user how to proceed.