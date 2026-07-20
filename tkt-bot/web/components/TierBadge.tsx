import styles from "./TierBadge.module.css";

/**
 * Badge tier dùng chung duy nhất (Amendment A3). Khai một chỗ, cấm khai rải:
 * chip, evidence sheet, landing đều gọi component này. Tâm chữ luôn đúng nhờ
 * display grid + place-items center + line-height 1.
 */
export default function TierBadge({
  tier,
  size = "sm",
}: {
  tier: "A" | "B" | "C";
  size?: "sm" | "lg";
}) {
  return (
    <span
      className={`${styles.badge} ${styles[size]} ${styles[`tier${tier}`]}`}
      aria-label={`Tier ${tier}`}
    >
      {tier}
    </span>
  );
}
