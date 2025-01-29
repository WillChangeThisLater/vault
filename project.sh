#!/bin/bash

cat <<EOF
I wrote a tiny CLI tool, `vault`, for securely
saving scripts and repositories that contain sensitive information

\`\`\`python
$(cat -n vault.py)
\`\`\`

I want to expand the script to include an optional description,
which can be provided when the user adds a script to the vault.
This description should show up when the user runs \`vault ls\`.
EOF
