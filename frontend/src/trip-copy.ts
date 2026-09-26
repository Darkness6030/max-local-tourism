import { money, nightsLabel } from "./lib";
import type { TripPlan } from "./types";

export const BUDGET_DISCLAIMER =
  "Ориентировочные расходы на всю группу. Цены мест, билетов и проживания уточняйте перед поездкой.";
export const ACCOMMODATION_DISCLAIMER =
  "Цены и свободные номера на ваши даты уточняйте у гостиницы.";
export const ITINERARY_DISCLAIMER =
  "Время программы рекомендательное. Время отправления и прибытия проверяйте в блоке транспорта; часы работы мест не подтверждены.";

export function budgetItemCopy(item: TripPlan["budget"]["items"][number], plan: TripPlan) {
  // Russian labels are supported for trips saved before the presentation moved here.
  if (item.category === "lodging" || item.category === "Проживание") {
    const stay = plan.accommodation;

    return {
      ...item,
      category: "Проживание",
      comment: stay
        ? `${stay.rooms} ном. × ${nightsLabel(stay.nights)} × ≈${money(stay.estimated_room_night_rub)}`
        : item.comment,
    };
  }

  if (item.category === "reserve" || item.category === "Небольшой запас") {
    return { ...item, category: "Небольшой запас", comment: "На непредвиденные расходы." };
  }

  return item;
}

export function tripNotices(plan: TripPlan): string[] {
  const notes = [...plan.warnings, ...plan.notes, ITINERARY_DISCLAIMER];

  if (plan.request.has_car) {
    notes.push("Расписание показано как альтернатива автомобилю; дорожный трафик не учтён.");
  }

  if (
    plan.estimated_travel_minutes != null &&
    plan.estimated_travel_minutes > plan.request.max_travel_minutes
  ) {
    notes.push("Расстояние по прямой может не уложиться в желаемое время дороги; проверьте маршрут.");
  }

  if (!plan.budget.within_budget) {
    notes.push(`Оценка с запасом превышает бюджет на ${plan.budget.estimated_total_rub - plan.budget.limit_rub} ₽.`);
  }

  if (plan.transport) {
    if (!plan.transport.outbound.length) {
      notes.push("После выбранного времени не найдено подходящих рейсов туда.");
    }

    if (!plan.transport.return_trip.length) {
      notes.push("После выбранного времени не найдено подходящих рейсов обратно.");
    }
  }

  return [...new Set(notes)];
}
