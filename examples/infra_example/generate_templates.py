import json
import os

from infra_example.jobs.tag_infra_example import tag_infra_example


def write_template(template):
    _template = json.loads(template)
    template_file = f'./stacks/{_template["//"]["metadata"]["stackName"]}/cdk.tf.json'
    os.makedirs(os.path.dirname(template_file), exist_ok=True)
    with open(template_file, "w") as f:
        f.write(template)


stacks = []
for tag in tag_infra_example.tags:
    if tag.startswith("infrastructure/"):
        write_template(tag_infra_example.tags[tag])

for solid in tag_infra_example.solids:
    for tag in solid.tags:
        if tag.startswith("infrastructure/"):
            write_template(solid.tags[tag])
