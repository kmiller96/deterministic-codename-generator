# Deterministic Codename Generator

Generates a codename, deterministically, for a given input.

## Why?

In my work, I often like to alias clients. That way, if I accidentally share my
screen where my client data is (e.g. Notion) it's less likely I'll leak sensitive
information such as who I work for.

Usually, my aliases link back to their name in some way. For example, if one of
my clients was [Suez](https://www.suez.com/en/waste) (for reference, they aren't)
then I might alias them as `CN: Canal` in reference to the Suez Canal.

This project doesn't aim to achieve such logical mappings. All codenames are
completely arbitrary.

## Deployment

You can run this server using fastapi:

```bash
uv run fastapi run
```

In practice, I deploy this in my homelab setup as a docker container in my docker
compose stack. This service's dockerfile can be found in this repo. If you wish
to run this service via docker:

```bash
docker build -t torrent-portal .
docker run --rm -it -p 8000:80 torrent-portal
```

## Development Quickstart

If you wish to poke around locally with this service, the easiest way is to do
this via fastapi's development server:

```bash
uv run fastapi dev
```

## TODO

- [ ] Deploy this on to my public server as a public prototype.
