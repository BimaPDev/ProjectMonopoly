"use client";

const ProfileImage = ({ name, size = 64 }: { name: string; size?: number }) => {
    const nameParts = name.split(" ");
    const firstNameInitial = nameParts[0] ? nameParts[0][0] : "";
    const lastNameInitial = nameParts[1] ? nameParts[1][0] : "";

    // Generate a consistent random color based on the name
    const getColorFromName = (name: string) => {
        let hash = 0;
        for (let i = 0; i < name.length; i++) {
            hash = name.charCodeAt(i) + ((hash << 5) - hash);
        }

        const colors = [
            "bg-red-500/90",
            "bg-orange-500/90",
            "bg-yellow-500/90",
            "bg-green-500/90",
            "bg-teal-500/90",
            "bg-blue-500/90",
            "bg-indigo-500/90",
            "bg-purple-500/90",
            "bg-pink-500/90",
            "bg-rose-500/90",
        ];

        const index = Math.abs(hash) % colors.length;
        return colors[index];
    };



    return (
        <span
            className={`user-profile-image bg-black text-white  text-xl font-semibold rounded-full text-center flex items-center justify-center`}
            style={{ width: `${size}px`, height: `${size}px` }}
        >
            {firstNameInitial}
            {lastNameInitial}
        </span>
    );
};
export default ProfileImage;