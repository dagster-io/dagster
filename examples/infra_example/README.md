# infra_example

[requires cdktf cli](https://learn.hashicorp.com/tutorials/terraform/cdktf-install)

## install

for cdktf providers run:

```bash
cdktf get
```

which will pull and generate python definitions for cdktf in `infra_example/resources/imports`

## generating tf stacks for the tag_infra_example

```bash
python generate_templates.py
```

which will create tf stacks in `stacks/`

each stack dir can then be initialized and deployed

```bash
terraform init
terraform apply
```
