**What happens**

Two tests fail on a Mac that has Google Fonts' Noto Serif installed in `~/Library/Fonts`. Google Fonts offers Noto Serif only as variable fonts (`NotoSerif-VariableFont_wdth,wght.ttf` and `NotoSerif-Italic-VariableFont_wdth,wght.ttf`), so anyone who installs it from there gets this. Seen on 0.14.0 (`main` at f37f20ff), macOS on Apple Silicon. The app itself works; only the tests disagree with it.

- `tests_text_edit::fonts_lists_bundled_and_installed_families` (`crates/engine/src/tests_text_edit.rs`): the style list for Noto Serif doesn't match what the test expects.
- `fonts::tests::bundled_families_and_resolution` (`crates/text/src/fonts.rs`, the assert at line 1016): `left: false, right: true` on `resolved.synth_bold`.

Removing the two Noto Serif files makes both pass.

**Why**

The app lists a variable face's named instances as styles (`fonts.rs` ~431: the face's own style, then `f.info.instances`), so the italic variable font offers Italic, Bold Italic, Light Italic and so on. The tests only look at each face's own style (`face.style`), so they see a single "Italic":

1. `fonts_lists_bundled_and_installed_families` builds `expected_styles` from `face.style` only, so the app's list (with the named instances) is longer than expected.
2. `bundled_families_and_resolution` looks for a face whose style is "Bold Italic", finds none, and expects the nearest face (Italic, weight 400) with a synthesized bold. The resolver instead picks the italic variable font's Bold Italic named instance, a real style, so it doesn't synthesize bold.

**Suggested fix**

1. In `tests_text_edit.rs`, count the named instances too:
   ```rust
   expected_styles.extend(
       installed.iter()
           .filter(|face| face.family.eq_ignore_ascii_case("Noto Serif"))
           .flat_map(|face| std::iter::once(face.style.clone()).chain(face.instances.iter().map(|i| i.style.clone()))),
   );
   ```
2. In `fonts.rs`'s `bundled_families_and_resolution`, treat a candidate with a "Bold Italic" named instance like a face whose own style is "Bold Italic" (the "real style wins" branch: no synthesized bold or italic).

We haven't made or run these changes; they're what the code suggests.
