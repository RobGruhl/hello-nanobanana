"""Command-line interface for nanobanana."""

import asyncio
import json
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from .config import ensure_output_dir, ensure_profiles_dir, PROFILES_DIR
from .generator import generate_image
from .batch import generate_batch
from .models.image import AspectRatio
from .models.profile import load_profile, list_profiles, GenerationProfile

console = Console()


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Gemini Image Generation CLI.

    Generate images using Google's Gemini models with adaptive rate limiting.
    """
    pass


@cli.command()
@click.argument("prompt")
@click.option("--output", "-o", required=True, help="Output file path")
@click.option("--aspect", "-a", default="2:3", help="Aspect ratio (2:3, 3:2, 1:1, 16:9, 9:16)")
@click.option("--model", "-m", default=None, help="Gemini model ID")
@click.option("--profile", "-p", default=None, help="Generation profile to use")
def generate(prompt: str, output: str, aspect: str, model: Optional[str], profile: Optional[str]):
    """Generate a single image from a text prompt.

    Examples:

        gemini-image generate "A sunset over mountains" -o sunset.png

        gemini-image generate "Hero portrait" --profile comic-panel -o hero.png

        gemini-image generate "Wide landscape" -o landscape.png --aspect 16:9
    """
    output_path = Path(output)

    # Validate aspect ratio
    try:
        AspectRatio.from_string(aspect)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    # Load profile if specified
    if profile:
        try:
            prof = load_profile(profile)
            console.print(f"[dim]Using profile: {prof.name}[/dim]")
        except FileNotFoundError:
            console.print(f"[red]Error: Profile '{profile}' not found[/red]")
            available = list_profiles()
            if available:
                console.print(f"[dim]Available profiles: {', '.join(available)}[/dim]")
            return

    console.print(f"[dim]Generating image...[/dim]")
    console.print(f"[dim]Prompt: {prompt[:80]}{'...' if len(prompt) > 80 else ''}[/dim]")

    try:
        result = generate_image(
            prompt=prompt,
            output=output_path,
            aspect_ratio=aspect,
            model=model,
            profile=profile,
        )
        console.print(f"[green]Generated: {result.path}[/green]")
        console.print(f"[dim]Size: {result.width}x{result.height}, Time: {result.generation_time:.1f}s[/dim]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.argument("prompts_file", type=click.Path(exists=True))
@click.option("--output-dir", "-o", required=True, help="Output directory")
@click.option("--concurrent", "-c", type=int, default=None, help="Max concurrent requests")
@click.option("--rpm", type=int, default=None, help="Requests per minute limit")
@click.option("--profile", "-p", default=None, help="Generation profile to use")
@click.option("--skip-existing/--no-skip", default=True, help="Skip existing files")
def batch(
    prompts_file: str,
    output_dir: str,
    concurrent: Optional[int],
    rpm: Optional[int],
    profile: Optional[str],
    skip_existing: bool,
):
    """Generate multiple images from a JSON file.

    The JSON file should contain an array of objects with "prompt" and
    optional "output" keys. If "output" is not specified, filenames are
    generated automatically.

    Example JSON format:

        [
            {"prompt": "A red dragon", "output": "dragon.png"},
            {"prompt": "A blue wizard"}
        ]

    Examples:

        gemini-image batch prompts.json -o ./images/

        gemini-image batch prompts.json -o ./images/ --concurrent 12
    """
    # Load prompts
    with open(prompts_file, "r") as f:
        prompts = json.load(f)

    if not isinstance(prompts, list):
        console.print("[red]Error: JSON file must contain an array of objects[/red]")
        return

    # Prepare items with output paths
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    items = []
    for i, item in enumerate(prompts):
        if isinstance(item, str):
            # Simple string prompt
            items.append({
                "prompt": item,
                "output": out_path / f"image_{i:04d}.png",
            })
        elif isinstance(item, dict):
            prompt = item.get("prompt")
            if not prompt:
                console.print(f"[yellow]Warning: Skipping item {i} - no prompt[/yellow]")
                continue

            output = item.get("output")
            if output:
                output_file = out_path / output
            else:
                output_file = out_path / f"image_{i:04d}.png"

            items.append({
                "prompt": prompt,
                "output": output_file,
            })

    console.print(f"[cyan]Batch Generation[/cyan]")
    console.print(f"[dim]Items: {len(items)}[/dim]")
    console.print(f"[dim]Output: {out_path}[/dim]")
    if concurrent:
        console.print(f"[dim]Concurrent: {concurrent}[/dim]")
    if profile:
        console.print(f"[dim]Profile: {profile}[/dim]")
    console.print()

    # Run batch
    try:
        results = asyncio.run(
            generate_batch(
                items=items,
                profile=profile,
                max_concurrent=concurrent,
                rpm_limit=rpm,
                skip_existing=skip_existing,
            )
        )
        console.print(f"\n[green]Completed: {len(results)}/{len(items)} images generated[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
def profiles():
    """List available generation profiles."""
    ensure_profiles_dir()
    available = list_profiles()

    if not available:
        console.print("[yellow]No profiles found.[/yellow]")
        console.print(f"[dim]Create profiles in: {PROFILES_DIR}[/dim]")
        return

    table = Table(title="Generation Profiles")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="bold")
    table.add_column("Aspect", style="green")
    table.add_column("Model", style="yellow")
    table.add_column("Description", style="dim")

    for profile_id in available:
        try:
            prof = load_profile(profile_id)
            desc = prof.description[:40] + "..." if len(prof.description) > 40 else prof.description
            table.add_row(
                prof.id,
                prof.name,
                prof.config.aspect_ratio.value,
                prof.config.model[:30] + "..." if len(prof.config.model) > 30 else prof.config.model,
                desc or "-",
            )
        except Exception as e:
            table.add_row(profile_id, "[red]Error[/red]", "-", "-", str(e)[:40])

    console.print(table)


@cli.command()
@click.argument("profile_id")
def info(profile_id: str):
    """Show detailed information about a profile."""
    try:
        prof = load_profile(profile_id)
    except FileNotFoundError:
        console.print(f"[red]Error: Profile '{profile_id}' not found[/red]")
        available = list_profiles()
        if available:
            console.print(f"[dim]Available profiles: {', '.join(available)}[/dim]")
        return

    console.print(f"\n[bold cyan]{prof.name}[/bold cyan] ({prof.id})")

    if prof.description:
        console.print(f"[dim]{prof.description}[/dim]\n")

    console.print("[bold]Configuration:[/bold]")
    console.print(f"  Model: {prof.config.model}")
    console.print(f"  Aspect Ratio: {prof.config.aspect_ratio.value}")

    if prof.style_prefix:
        console.print("\n[bold]Style Prefix:[/bold]")
        console.print(Panel(prof.style_prefix, border_style="dim"))

    if prof.style_suffix:
        console.print("\n[bold]Style Suffix:[/bold]")
        console.print(Panel(prof.style_suffix, border_style="dim"))

    # Show example formatted prompt
    console.print("\n[bold]Example Prompt Formatting:[/bold]")
    example = prof.format_prompt("Your prompt here")
    console.print(Panel(example, border_style="green"))


@cli.command()
@click.option("--prompt", "-p", default="A beautiful sunset over mountains with vibrant colors", help="Test prompt")
@click.option("--output", "-o", default=None, help="Output file (default: test_output.png)")
def test(prompt: str, output: Optional[str]):
    """Quick test with a sample prompt.

    Generates a single image to verify the API connection and setup.
    """
    output_path = Path(output) if output else ensure_output_dir() / "test_output.png"

    console.print("[cyan]Running API Test[/cyan]")
    console.print(f"[dim]Prompt: {prompt}[/dim]")
    console.print(f"[dim]Output: {output_path}[/dim]")
    console.print()

    try:
        result = generate_image(prompt=prompt, output=output_path)
        console.print(f"[green]Success![/green]")
        console.print(f"[dim]Generated: {result.path}[/dim]")
        console.print(f"[dim]Size: {result.width}x{result.height}[/dim]")
        console.print(f"[dim]Time: {result.generation_time:.1f}s[/dim]")
        console.print(f"[dim]Model: {result.model}[/dim]")
    except ValueError as e:
        if "GOOGLE_API_KEY" in str(e):
            console.print("[red]Error: GOOGLE_API_KEY not set[/red]")
            console.print("[dim]Set GOOGLE_API_KEY in .env file or as environment variable[/dim]")
        else:
            console.print(f"[red]Error: {e}[/red]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
def aspect_ratios():
    """Show available aspect ratios."""
    table = Table(title="Available Aspect Ratios")
    table.add_column("Name", style="cyan")
    table.add_column("Value", style="bold")
    table.add_column("Use Case", style="dim")

    use_cases = {
        "PORTRAIT": "Portraits, characters, mobile screens",
        "LANDSCAPE": "Scenes, landscapes, desktop backgrounds",
        "SQUARE": "Social media, icons, thumbnails",
        "WIDE": "Cinematic, panoramas, video thumbnails",
        "TALL": "Stories, mobile full-screen, posters",
    }

    for ratio in AspectRatio:
        table.add_row(ratio.name, ratio.value, use_cases.get(ratio.name, "-"))

    console.print(table)


if __name__ == "__main__":
    cli()
