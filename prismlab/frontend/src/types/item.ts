export interface Item {
  id: number;
  name: string;
  internal_name: string;
  cost: number | null;
  components: string[] | null;
  is_recipe: boolean;
  is_neutral: boolean;
  tier: number | null;
  bonuses: Record<string, unknown>[] | null;
  active_desc: string | null;
  passive_desc: string | null;
  category: string | null;
  tags: string[] | null;
  img_url: string;
}
