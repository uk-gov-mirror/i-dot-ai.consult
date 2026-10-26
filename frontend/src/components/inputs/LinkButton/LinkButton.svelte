<script lang="ts">
  import clsx from "clsx";

  import type { Snippet } from "svelte";

  interface Props {
    children: Snippet;
    href?: string;
    handleClick?: () => void;
    disabled?: boolean;
    ariaLabel?: string;
    ariaExpanded?: boolean;
    inline?: boolean;
  }

  let {
    children,
    href,
    handleClick,
    disabled = false,
    ariaLabel,
    ariaExpanded,
    inline = false,
  }: Props = $props();
</script>

<svelte:element
  this={href ? "a" : "button"}
  type={href ? undefined : "button"}
  href={href || undefined}
  class={clsx([
    "text-sm text-primary underline underline-offset-2",
    "focus-visible:outline-2 focus-visible:outline-yellow-300",
    "disabled:cursor-not-allowed disabled:opacity-50",
    inline ? "ml-2" : "mt-2 block",
  ])}
  disabled={href ? undefined : disabled}
  aria-label={ariaLabel}
  aria-expanded={ariaExpanded}
  onclick={() => {
    if (!disabled) handleClick?.();
  }}
>
  {@render children()}
</svelte:element>
