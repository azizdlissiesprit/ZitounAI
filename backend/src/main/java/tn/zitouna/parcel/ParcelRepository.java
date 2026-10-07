package tn.zitouna.parcel;

import java.util.List;
import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;

public interface ParcelRepository extends JpaRepository<Parcel, Long> {

    List<Parcel> findByOwnerIdOrderByCreatedAtDesc(Long ownerId);

    Optional<Parcel> findByIdAndOwnerId(Long id, Long ownerId);
}
