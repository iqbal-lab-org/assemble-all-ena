import json

def run(options):
    with open(options.infile) as f:
        d = json.load(f)

    for sample in d:
        d[sample]['ignore'] = not d[sample]['asm']

    with open(options.outfile, 'w') as f:
        d = json.dump(d, f, indent=2, sort_keys=True)

