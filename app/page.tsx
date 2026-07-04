"use client";

import { FormEvent, KeyboardEvent, ReactNode, useEffect, useMemo, useState } from "react";

type Recipe = {
  id: string;
  title: string;
  subtitle: string;
  image: string;
  imageSource: "url" | "generated" | "file";
  story: string;
  ingredients: string[];
  steps: string[];
  notes: string;
  prepTime: string;
  cookTime: string;
  serves: string;
  tags: string[];
  favourite: boolean;
  createdAt: string;
};

type ViewState = "cover" | "gallery" | "detail" | "add" | "activeCook";
type Toast = { type: "success" | "error" | "neutral"; message: string } | null;
type FormErrors = Partial<Record<"title" | "ingredients" | "steps", string>>;

const starterRecipes: Recipe[] = [
  {
    id: "sunday-sugo",
    title: "Sunday Tomato Sugo",
    subtitle: "Slow red sauce for a long table",
    image: "tomato",
    imageSource: "generated",
    story: "This is the pot that starts before lunch and waits patiently for everyone to arrive. The sauce is forgiving, deep, and best when someone tears bread too early.",
    ingredients: ["2 tbsp olive oil", "1 brown onion, finely diced", "4 garlic cloves, crushed", "2 tins crushed tomatoes", "1 parmesan rind", "Handful basil leaves", "Salt and cracked pepper"],
    steps: ["Warm the oil in a heavy pot and soften the onion until sweet and translucent.", "Stir in garlic for one minute, then add tomatoes, parmesan rind, salt, and pepper.", "Simmer gently for 45 minutes, stirring whenever the kitchen smells too good to ignore.", "Tear basil through the sugo and serve with pasta or spoon over grilled bread."],
    notes: "Nonna always added a pinch of sugar if the tomatoes were sharp.",
    prepTime: "15 min",
    cookTime: "55 min",
    serves: "6",
    tags: ["Italian", "Slow", "Family"],
    favourite: true,
    createdAt: "2026-01-12",
  },
  {
    id: "campfire-damper",
    title: "Campfire Damper",
    subtitle: "Bush bread with a smoky crust",
    image: "damper",
    imageSource: "generated",
    story: "A simple loaf for tin mugs of tea, wrapped in a cloth and passed around while the coals settle. It likes rough hands and does not mind imperfect measuring.",
    ingredients: ["3 cups self-raising flour", "1 tsp salt", "60 g cold butter", "1 cup milk", "Extra flour for dusting", "Golden syrup to serve"],
    steps: ["Rub butter into flour and salt until the bowl looks like coarse sand.", "Pour in milk and bring together with a butter knife, stopping before the dough becomes tough.", "Shape into a round, score the top, and nestle in a camp oven over gentle coals.", "Bake for 25 minutes, turning once, until hollow-sounding and deeply golden."],
    notes: "If cooking indoors, bake at 200°C in a cast iron pan.",
    prepTime: "10 min",
    cookTime: "25 min",
    serves: "8",
    tags: ["Campfire", "Bread", "Simple"],
    favourite: false,
    createdAt: "2026-02-03",
  },
  {
    id: "lemon-rosemary-chicken",
    title: "Lemon Rosemary Chicken",
    subtitle: "Bright roast chicken for easy Sundays",
    image: "chicken",
    imageSource: "generated",
    story: "The lemon perfumes the pan juices and the rosemary crisps at the edges. It is the kind of meal that makes potatoes feel like an occasion.",
    ingredients: ["1 whole chicken", "2 lemons", "4 rosemary sprigs", "3 tbsp olive oil", "6 garlic cloves", "1 kg baby potatoes", "Sea salt"],
    steps: ["Pat the chicken dry, then rub with oil, salt, lemon zest, and chopped rosemary.", "Fill the cavity with lemon halves and garlic, then place over potatoes in a roasting tray.", "Roast at 210°C for 20 minutes, then lower to 180°C and cook until the juices run clear.", "Rest for 15 minutes before carving and spooning over the lemony pan juices."],
    notes: "Scatter olives in the tray for the final 20 minutes when serving guests.",
    prepTime: "20 min",
    cookTime: "1 hr 15 min",
    serves: "4",
    tags: ["Roast", "Chicken", "Sunday"],
    favourite: true,
    createdAt: "2026-03-18",
  },
  {
    id: "spiced-apple-crumble",
    title: "Spiced Apple Crumble",
    subtitle: "Cinnamon apples under oat rubble",
    image: "apple",
    imageSource: "generated",
    story: "A pudding for cold windows and second helpings. The apples collapse into syrup while the topping stays craggy, buttery, and spoon-stealing crisp.",
    ingredients: ["6 tart apples", "2 tbsp brown sugar", "1 tsp cinnamon", "1/2 tsp ginger", "1 cup rolled oats", "3/4 cup plain flour", "100 g butter", "Cream to serve"],
    steps: ["Slice apples and toss with sugar, cinnamon, and ginger in a baking dish.", "Rub butter into oats and flour until clumpy, then tumble over the apples.", "Bake at 180°C for 35 minutes until bubbling at the edges and bronzed on top.", "Rest for 10 minutes and serve with cold cream."],
    notes: "A handful of blackberries makes this taste like late autumn.",
    prepTime: "18 min",
    cookTime: "35 min",
    serves: "6",
    tags: ["Dessert", "Autumn", "Comfort"],
    favourite: false,
    createdAt: "2026-04-09",
  },
];

const Icon = ({ children }: { children: ReactNode }) => <span className="inline-flex h-5 w-5 items-center justify-center" aria-hidden="true">{children}</span>;
const icons = { book: <Icon>📖</Icon>, plus: <Icon>✚</Icon>, heart: <Icon>♥</Icon>, clock: <Icon>◷</Icon>, chef: <Icon>🍳</Icon>, back: <Icon>←</Icon>, check: <Icon>✓</Icon>, upload: <Icon>▣</Icon> };


function TactileButton({ children, variant = "primary", disabled, loading, onClick, type = "button", className = "", ariaLabel }: { children: ReactNode; variant?: "primary" | "secondary" | "ghost" | "destructive"; disabled?: boolean; loading?: boolean; onClick?: () => void; type?: "button" | "submit"; className?: string; ariaLabel?: string }) {
  return <button aria-label={ariaLabel} type={type} disabled={disabled || loading} onClick={onClick} className={`tactile-button ${variant} ${className}`}>{loading ? "Saving..." : children}</button>;
}

function InkField({ label, value, onChange, textarea, error, helper, placeholder, disabled }: { label: string; value: string; onChange: (value: string) => void; textarea?: boolean; error?: string; helper?: string; placeholder?: string; disabled?: boolean }) {
  const id = label.toLowerCase().replace(/\W+/g, "-");
  const Field = textarea ? "textarea" : "input";
  return <label className="block" htmlFor={id}><span className="mb-2 block font-semibold text-[var(--ink)]">{label}</span><Field id={id} disabled={disabled} value={value} onChange={(event) => onChange(event.target.value)} placeholder={placeholder} className={`ink-field ${textarea ? "min-h-28" : ""} ${error ? "field-error" : ""}`} />{helper ? <span className="mt-1 block text-sm text-[var(--mutedInk)]">{helper}</span> : null}{error ? <span className="mt-1 block text-sm font-semibold text-[var(--cranberry)]">{error}</span> : null}</label>;
}

function PaperToast({ toast }: { toast: Toast }) {
  return <div aria-live="polite" className="fixed right-4 top-4 z-50 max-w-sm">{toast ? <div className={`paper-toast ${toast.type}`}>{toast.message}</div> : null}</div>;
}

function PageSkeleton() { return <div className="page-skeleton"><div /><div /><div /></div>; }
function EmptyState({ onAdd }: { onAdd: () => void }) { return <section className="paper-panel text-center"><h2 className="text-2xl font-bold">The ledger is waiting for its first recipe.</h2><p className="mt-2 text-[var(--mutedInk)]">Add a family dish and it will appear here as a tucked-in card.</p><TactileButton onClick={onAdd} className="mt-5">{icons.plus} Add a recipe</TactileButton></section>; }

function BookShell({ children }: { children: ReactNode }) { return <div className="tabletop min-h-screen px-4 py-5 text-[var(--ink)] sm:px-6 lg:py-8"><div className="mx-auto max-w-7xl">{children}</div></div>; }
function BookmarkNav({ view, goGallery, goAdd }: { view: ViewState; goGallery: () => void; goAdd: () => void }) { return <nav aria-label="Ledger navigation" className="bookmark-nav"><button onClick={goGallery} className={view === "gallery" ? "active" : ""}>📚 Recipes</button><button onClick={goAdd} className={view === "add" ? "active" : ""}>✚ Add</button></nav>; }

function RecipeImage({ recipe, large = false }: { recipe: Recipe; large?: boolean }) {
  const uploadedStyle = recipe.imageSource === "url" && recipe.image ? { backgroundImage: `linear-gradient(rgba(43, 26, 18, .08), rgba(43, 26, 18, .18)), url(${recipe.image})` } : undefined;

  return (
    <div className={`recipe-art ${recipe.image} ${large ? "large" : ""}`} style={uploadedStyle} role="img" aria-label={`${recipe.title} illustration`}>
      <span>{recipe.title}</span>
    </div>
  );
}

function RecipeCard({ recipe, onOpen, onFavourite, index }: { recipe: Recipe; onOpen: () => void; onFavourite: () => void; index: number }) {
  const onKey = (event: KeyboardEvent<HTMLElement>) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); onOpen(); } };
  return <article tabIndex={0} onKeyDown={onKey} onClick={onOpen} className="polaroid-card" style={{ rotate: `${[-1.4, 1.1, -0.6, 1.6][index % 4]}deg` }} aria-label={`Open ${recipe.title}`}><RecipeImage recipe={recipe} /><div className="mt-4 flex items-start justify-between gap-3"><div><h3 className="text-xl font-black">{recipe.title}</h3><p className="text-sm text-[var(--mutedInk)]">{recipe.subtitle}</p></div><button className="heart-button" onClick={(event) => { event.stopPropagation(); onFavourite(); }} aria-label={`${recipe.favourite ? "Remove" : "Add"} ${recipe.title} favourite`}>{recipe.favourite ? "♥" : "♡"}</button></div><div className="mt-3 flex flex-wrap gap-2">{recipe.tags.map((tag) => <span className="tag" key={tag}>{tag}</span>)}</div><p className="mt-3 text-sm text-[var(--mutedInk)]">{icons.clock} Prep {recipe.prepTime} · Cook {recipe.cookTime}</p></article>;
}

function RecipeGallery({ recipes, openRecipe, toggleFavourite, onAdd, isLoading }: { recipes: Recipe[]; openRecipe: (id: string) => void; toggleFavourite: (id: string) => void; onAdd: () => void; isLoading: boolean }) {
  return <section className="ledger-page page-motion"><div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between"><div><p className="eyebrow">Recipe gallery</p><h1 className="text-4xl font-black">Cards tucked between parchment pages</h1><p className="mt-2 max-w-2xl text-[var(--mutedInk)]">Choose a dish, mark a favourite, or add a new memory to the family ledger.</p></div><TactileButton onClick={onAdd}>{icons.plus} Add family recipe</TactileButton></div>{isLoading ? <PageSkeleton /> : recipes.length ? <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-4">{recipes.map((recipe, index) => <RecipeCard key={recipe.id} recipe={recipe} index={index} onOpen={() => openRecipe(recipe.id)} onFavourite={() => toggleFavourite(recipe.id)} />)}</div> : <EmptyState onAdd={onAdd} />}</section>;
}

function RecipeDetail({ recipe, onBack, onFavourite, onNotes, onCook }: { recipe: Recipe; onBack: () => void; onFavourite: () => void; onNotes: (notes: string) => void; onCook: () => void }) {
  return <section className="book-spread page-motion"><div className="spread-page"><TactileButton variant="ghost" onClick={onBack}>{icons.back} Back to gallery</TactileButton><RecipeImage recipe={recipe} large /><p className="eyebrow mt-6">{recipe.tags.join(" · ")}</p><h1 className="text-4xl font-black">{recipe.title}</h1><p className="mt-2 text-lg text-[var(--mutedInk)]">{recipe.subtitle}</p><div className="my-5 grid grid-cols-3 gap-3 text-sm"><span className="meta-chip">Prep<br /><b>{recipe.prepTime}</b></span><span className="meta-chip">Cook<br /><b>{recipe.cookTime}</b></span><span className="meta-chip">Serves<br /><b>{recipe.serves}</b></span></div><p className="leading-7">{recipe.story}</p><h2 className="mt-6 text-2xl font-black">Ingredients</h2><ul className="mt-3 space-y-2">{recipe.ingredients.map((item) => <li key={item}>• {item}</li>)}</ul></div><div className="spread-page right-page"><div className="flex flex-wrap gap-3"><TactileButton variant="secondary" onClick={onFavourite}>{icons.heart} {recipe.favourite ? "Favourited" : "Favourite"}</TactileButton><TactileButton onClick={onCook}>{icons.chef} Start cooking</TactileButton></div><h2 className="mt-8 text-2xl font-black">Method</h2><ol className="mt-4 space-y-4">{recipe.steps.map((step, index) => <li className="method-step" key={step}><b>{index + 1}</b><span>{step}</span></li>)}</ol><div className="mt-8"><InkField label="Family notes" textarea value={recipe.notes} onChange={onNotes} helper="Changes are saved in this browser session." /></div></div></section>;
}

function AddRecipePanel({ onCancel, onSave, errors, isSubmitting }: { onCancel: () => void; onSave: (recipe: Recipe) => void; errors: FormErrors; isSubmitting: boolean }) {
  const [form, setForm] = useState({ title: "", subtitle: "", image: "", story: "", ingredients: "", steps: "", notes: "", prepTime: "", cookTime: "", serves: "", tags: "" });
  const [fileName, setFileName] = useState("");
  const set = (key: keyof typeof form) => (value: string) => setForm((current) => ({ ...current, [key]: value }));
  function submit(event: FormEvent) { event.preventDefault(); onSave({ id: `${Date.now()}`, title: form.title.trim(), subtitle: form.subtitle.trim() || "A newly tucked family favourite", image: fileName ? "file" : form.image || "tomato", imageSource: fileName ? "file" : form.image ? "url" : "generated", story: form.story.trim() || "A recipe added to the ledger with room for more story next time.", ingredients: form.ingredients.split("\n").map((x) => x.trim()).filter(Boolean), steps: form.steps.split("\n").map((x) => x.trim()).filter(Boolean), notes: form.notes, prepTime: form.prepTime || "Soon", cookTime: form.cookTime || "Until ready", serves: form.serves || "4", tags: form.tags.split(",").map((x) => x.trim()).filter(Boolean), favourite: false, createdAt: new Date().toISOString() }); }
  return <section className="add-drawer"><form onSubmit={submit} className="ledger-page mx-auto max-w-4xl"><div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between"><div><p className="eyebrow">New page</p><h1 className="text-4xl font-black">Add a family recipe</h1><p className="mt-2 text-[var(--mutedInk)]">Newline ingredients and method steps. Required fields are marked by validation below.</p></div><TactileButton variant="ghost" onClick={onCancel}>Cancel</TactileButton></div><div className="grid gap-5 md:grid-cols-2"><InkField label="Title" value={form.title} onChange={set("title")} error={errors.title} placeholder="Aunt May's soup" /><InkField label="Subtitle" value={form.subtitle} onChange={set("subtitle")} placeholder="A short, warm description" /><InkField label="Image URL" value={form.image} onChange={set("image")} helper="Optional. A parchment illustration appears if it cannot be shown." /><label className="block"><span className="mb-2 block font-semibold">Optional file preview</span><input className="ink-field" type="file" accept="image/*" onChange={(event) => setFileName(event.target.files?.[0]?.name ?? "")} />{fileName ? <span className="mt-1 block text-sm text-[var(--sage)]">{icons.upload} Preview ready: {fileName}</span> : null}</label><InkField label="Prep time" value={form.prepTime} onChange={set("prepTime")} /><InkField label="Cook time" value={form.cookTime} onChange={set("cookTime")} /><InkField label="Serves" value={form.serves} onChange={set("serves")} /><InkField label="Tags" value={form.tags} onChange={set("tags")} helper="Comma-separated, e.g. Winter, Soup" /><div className="md:col-span-2"><InkField label="Story" textarea value={form.story} onChange={set("story")} /></div><InkField label="Ingredients" textarea value={form.ingredients} onChange={set("ingredients")} error={errors.ingredients} helper="One ingredient per line." /><InkField label="Steps" textarea value={form.steps} onChange={set("steps")} error={errors.steps} helper="One method step per line." /><div className="md:col-span-2"><InkField label="Notes" textarea value={form.notes} onChange={set("notes")} /></div></div><div className="mt-8 flex flex-col gap-3 sm:flex-row sm:justify-end"><TactileButton variant="secondary" onClick={onCancel}>Return without saving</TactileButton><TactileButton type="submit" loading={isSubmitting}>{icons.check} Save recipe</TactileButton></div></form></section>;
}

function ActiveCookMode({ recipe, stepIndex, checked, setStep, toggleIngredient, onExit }: { recipe: Recipe; stepIndex: number; checked: Set<string>; setStep: (index: number) => void; toggleIngredient: (item: string) => void; onExit: () => void }) {
  const progress = Math.round(((stepIndex + 1) / recipe.steps.length) * 100);
  return <main className="cook-mode"><div className="mx-auto grid min-h-screen max-w-6xl gap-6 p-4 lg:grid-cols-[1.3fr_0.7fr] lg:p-8"><section className="cook-card"><p className="eyebrow">Active cook mode</p><h1 className="text-3xl font-black">{recipe.title}</h1><div className="mt-6 h-3 rounded-full bg-stone-200"><div className="h-full rounded-full bg-[var(--sage)]" style={{ width: `${progress}%` }} /></div><p className="mt-2 font-semibold">Step {stepIndex + 1} of {recipe.steps.length}</p><p className="my-8 text-3xl font-black leading-tight sm:text-5xl">{recipe.steps[stepIndex]}</p><div className="grid gap-3 sm:grid-cols-3"><TactileButton variant="secondary" disabled={stepIndex === 0} onClick={() => setStep(stepIndex - 1)}>Previous step</TactileButton><TactileButton disabled={stepIndex === recipe.steps.length - 1} onClick={() => setStep(stepIndex + 1)}>Next step</TactileButton><TactileButton variant="ghost" onClick={onExit}>Exit cook mode</TactileButton></div></section><aside className="cook-card"><h2 className="text-2xl font-black">Ingredient checklist</h2><div className="mt-5 space-y-3">{recipe.ingredients.map((item) => <label key={item} className="ingredient-check"><input type="checkbox" checked={checked.has(item)} onChange={() => toggleIngredient(item)} /><span>{item}</span></label>)}</div></aside></div></main>;
}

export default function App() {
  const [view, setView] = useState<ViewState>("cover");
  const [recipes, setRecipes] = useState(starterRecipes);
  const [selectedRecipeId, setSelectedRecipeId] = useState(starterRecipes[0].id);
  const [toast, setToast] = useState<Toast>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [formErrors, setFormErrors] = useState<FormErrors>({});
  const [activeStepIndex, setActiveStepIndex] = useState(0);
  const [checkedIngredients, setCheckedIngredients] = useState<Set<string>>(new Set());
  const [isSubmitting, setIsSubmitting] = useState(false);
  const selectedRecipe = useMemo(() => recipes.find((recipe) => recipe.id === selectedRecipeId) ?? recipes[0], [recipes, selectedRecipeId]);
  useEffect(() => { if (toast) { const id = window.setTimeout(() => setToast(null), 3200); return () => window.clearTimeout(id); } }, [toast]);
  function openGallery() { setIsLoading(true); setView("gallery"); window.setTimeout(() => setIsLoading(false), 450); }
  function openRecipe(id: string) { setSelectedRecipeId(id); setView("detail"); }
  function toggleFavourite(id = selectedRecipeId) { setRecipes((items) => items.map((recipe) => recipe.id === id ? { ...recipe, favourite: !recipe.favourite } : recipe)); setToast({ type: "neutral", message: "Favourite ribbon updated." }); }
  function saveNotes(notes: string) { setRecipes((items) => items.map((recipe) => recipe.id === selectedRecipeId ? { ...recipe, notes } : recipe)); }
  function saveRecipe(recipe: Recipe) { const errors: FormErrors = {}; if (!recipe.title) errors.title = "Title is required so the ledger can find this recipe again."; if (!recipe.ingredients.length) errors.ingredients = "Add at least one ingredient, one per line."; if (!recipe.steps.length) errors.steps = "Add at least one method step, one per line."; setFormErrors(errors); if (Object.keys(errors).length) { setToast({ type: "error", message: "A recipe needs a little more ink before it can be saved." }); return; } setIsSubmitting(true); window.setTimeout(() => { setRecipes((items) => [recipe, ...items]); setSelectedRecipeId(recipe.id); setIsSubmitting(false); setToast({ type: "success", message: "Recipe tucked into the ledger." }); setView("gallery"); }, 500); }
  function startCooking() { setActiveStepIndex(0); setCheckedIngredients(new Set()); setView("activeCook"); }
  if (view === "activeCook") return <ActiveCookMode recipe={selectedRecipe} stepIndex={activeStepIndex} checked={checkedIngredients} setStep={setActiveStepIndex} onExit={() => setView("detail")} toggleIngredient={(item) => setCheckedIngredients((current) => { const next = new Set(current); next.has(item) ? next.delete(item) : next.add(item); return next; })} />;
  return <BookShell><PaperToast toast={toast} /><BookmarkNav view={view} goGallery={openGallery} goAdd={() => setView("add")} />{view === "cover" ? <main className="cover"><div className="leather-cover"><p className="eyebrow text-amber-100">A digital cooking heirloom</p><h1>The Rustic Ledger</h1><p>Premium parchment pages for recipes, notes, favourites, and calm kitchen guidance.</p><div className="mt-8 flex flex-col gap-3 sm:flex-row"><TactileButton onClick={openGallery}>{icons.book} Open Ledger</TactileButton><TactileButton variant="secondary" onClick={() => setView("add")}>{icons.plus} Add a family recipe</TactileButton></div></div></main> : null}{view === "gallery" ? <RecipeGallery recipes={recipes} openRecipe={openRecipe} toggleFavourite={toggleFavourite} onAdd={() => setView("add")} isLoading={isLoading} /> : null}{view === "detail" && selectedRecipe ? <RecipeDetail recipe={selectedRecipe} onBack={openGallery} onFavourite={() => toggleFavourite()} onNotes={saveNotes} onCook={startCooking} /> : null}{view === "add" ? <AddRecipePanel onCancel={openGallery} onSave={saveRecipe} errors={formErrors} isSubmitting={isSubmitting} /> : null}</BookShell>;
}
