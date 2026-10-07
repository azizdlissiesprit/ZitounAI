package tn.zitouna.history;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.JpaRepository;

public interface PredictionRepository extends JpaRepository<PredictionRecord, Long> {

    @EntityGraph(attributePaths = "parcel")
    Page<PredictionRecord> findByUserIdOrderByCreatedAtDesc(Long userId, Pageable pageable);

    @EntityGraph(attributePaths = "parcel")
    Page<PredictionRecord> findByUserIdAndTypeOrderByCreatedAtDesc(Long userId, PredictionType type, Pageable pageable);
}
